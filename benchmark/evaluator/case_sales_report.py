import random
import sqlite3
import unittest
from pathlib import Path


COLUMNS = ['customer_id', 'name', 'paid_order_count', 'gross_cents', 'refunded_cents', 'net_cents']
SCHEMA = '''
CREATE TABLE customers (customer_id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE order_items (item_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, quantity INTEGER, unit_price_cents INTEGER);
CREATE TABLE refunds (refund_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, amount_cents INTEGER);
'''


class SalesTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.addCleanup(self.conn.close)
        self.conn.executescript(SCHEMA)
        self.sql = Path('/submission/report.sql').read_text()

    def seed(self, customers=(), orders=(), items=(), refunds=()):
        self.conn.executemany('INSERT INTO customers VALUES (?,?)', customers)
        self.conn.executemany('INSERT INTO orders VALUES (?,?,?)', orders)
        self.conn.executemany('INSERT INTO order_items VALUES (?,?,?,?)', items)
        self.conn.executemany('INSERT INTO refunds VALUES (?,?,?)', refunds)
        self.conn.commit()

    def run_query(self):
        # SQLite authorizer enforces read-only access; no lexical SELECT shortcut.
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
        self.conn.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
        self.conn.set_progress_handler(lambda: 1, 1000000)
        try:
            cursor = self.conn.execute(self.sql)
            self.assertEqual([column[0] for column in cursor.description], COLUMNS)
            rows = cursor.fetchall()
            for row in rows:
                self.assertTrue(all(isinstance(value, int) for value in row[2:]), 'Counts and cents must be integers')
            return rows
        finally:
            self.conn.set_authorizer(None)
            self.conn.set_progress_handler(None, 0)

    def test_totals_with_fanout(self):
        self.seed([('C', 'Shop')], [('O', 'C', 'paid')],
                  [('I1', 'O', 2, 500), ('I2', 'O', 1, 1000)],
                  [('R1', 'O', 100), ('R2', 'O', 200)])
        self.assertEqual(self.run_query(), [('C', 'Shop', 1, 2000, 300, 1700)])

    def test_equal_amount_events(self):
        self.seed([('C', 'Shop')], [('O', 'C', 'paid')],
                  [('I1', 'O', 1, 500), ('I2', 'O', 1, 500)],
                  [('R1', 'O', 100), ('R2', 'O', 100)])
        self.assertEqual(self.run_query(), [('C', 'Shop', 1, 1000, 200, 800)])

    def test_customers_without_paid_orders(self):
        self.seed([('C', 'Pending'), ('A', 'None'), ('B', 'Cancelled'), ('D', 'Empty order')],
                  [('O1', 'C', 'pending'), ('O2', 'B', 'cancelled'), ('O3', 'D', 'paid')],
                  [('I1', 'O1', 1, 100), ('I2', 'O2', 1, 200)], [('R1', 'O2', 20)])
        self.assertEqual(self.run_query(), [('A', 'None', 0, 0, 0, 0), ('B', 'Cancelled', 0, 0, 0, 0),
                                            ('C', 'Pending', 0, 0, 0, 0), ('D', 'Empty order', 1, 0, 0, 0)])

    def test_multiple_orders_and_names(self):
        self.seed([('A', 'Same'), ('B', 'Same')],
                  [('O1', 'A', 'paid'), ('O2', 'A', 'paid'), ('O3', 'B', 'paid')],
                  [('I1', 'O1', 1, 50), ('I2', 'O2', 2, 75), ('I3', 'O3', 1, 10)])
        self.assertEqual(self.run_query(), [('A', 'Same', 2, 200, 0, 200), ('B', 'Same', 1, 10, 0, 10)])

    def test_empty_database(self):
        self.assertEqual(self.run_query(), [])

    def test_property_generated_data(self):
        rng = random.Random(205)
        customers = [(f'C{i:02}', f'Name{i % 2}') for i in range(10)]
        orders, items, refunds = [], [], []
        totals = {key: [key, name, 0, 0, 0, 0] for key, name in customers}
        for n in range(60):
            key = rng.choice(customers)[0]
            status = rng.choice(['paid', 'pending', 'cancelled'])
            order_id = f'O{n}'
            orders.append((order_id, key, status))
            gross = refunded = 0
            for j in range(rng.randrange(4)):
                quantity, price = rng.randrange(1, 5), rng.randrange(1000)
                items.append((f'I{n}-{j}', order_id, quantity, price))
                gross += quantity * price
            for j in range(rng.randrange(4)):
                amount = rng.randrange(1 + gross // 4)
                refunds.append((f'R{n}-{j}', order_id, amount))
                refunded += amount
            if status == 'paid':
                totals[key][2] += 1
                totals[key][3] += gross
                totals[key][4] += refunded
                totals[key][5] += gross - refunded
        self.seed(customers, orders, items, refunds)
        self.assertEqual(self.run_query(), [tuple(totals[key]) for key in sorted(totals)])

    def test_constraint_read_only_query(self):
        self.seed([('A', 'Shop')])
        before = list(self.conn.iterdump())
        self.run_query()
        self.assertEqual(list(self.conn.iterdump()), before)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'rows': [['C01', 'Aurora', 1, 2000, 300, 1700], ['C02', 'Aurora', 0, 0, 0, 0], ['C03', 'Boreale', 0, 0, 0, 0]]}})
            self.assertEqual(json.loads((Path(temporary)/'result.json').read_text()), canonical)

    def test_constraint_workflow_failure_preserves_last_result(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary)/'result.json'
            artifact.write_text('last-valid-result')
            job = json.loads(Path('/submission/fixtures/rejected-job.json').read_text())
            receipt = consume(job, temporary)
            self.assertEqual(receipt, {'job_id': job['job_id'], 'status': 'failed', 'result': None})
            self.assertEqual(artifact.read_text(), 'last-valid-result')

    def test_constraint_workflow_failed_followup(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            good = json.loads(Path('/submission/fixtures/job.json').read_text())
            bad = json.loads(Path('/submission/fixtures/rejected-job.json').read_text())
            self.assertEqual(consume(good, temporary)['status'], 'completed')
            artifact = Path(temporary)/'result.json'
            previous = artifact.read_bytes()
            self.assertEqual(consume(bad, temporary), {'job_id': bad['job_id'], 'status': 'failed', 'result': None})
            self.assertEqual(artifact.read_bytes(), previous)
