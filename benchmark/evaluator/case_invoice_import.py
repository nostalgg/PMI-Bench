import csv
import importlib
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path


FIELDS = ['invoice_id', 'customer_id', 'amount_cents', 'status']


class InvoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'invoices.db'
        self.csv = self.root / 'incoming.csv'
        self.run_import = importlib.import_module('importer').import_invoices
        with sqlite3.connect(self.db) as conn:
            conn.execute('CREATE TABLE invoices (invoice_id TEXT PRIMARY KEY, '
                         'customer_id TEXT NOT NULL, amount_cents INTEGER NOT NULL, '
                         'status TEXT NOT NULL)')

    def write(self, rows, fields=FIELDS):
        with self.csv.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(fields)
            writer.writerows(rows)

    def rows(self):
        with sqlite3.connect(self.db) as conn:
            return conn.execute('SELECT * FROM invoices ORDER BY invoice_id').fetchall()

    def test_insert_preserves_identifiers(self):
        self.write([(' 0007 ', ' 001 ', ' 12000 ', ' paid '), ('A', 'B', '0', 'issued')])
        self.assertEqual(self.run_import(self.csv, self.db), 2)
        self.assertEqual(self.rows(), [('0007', '001', 12000, 'paid'), ('A', 'B', 0, 'issued')])

    def test_repeat_updates_last_wins(self):
        self.write([('A', 'C', '100', 'issued')])
        self.run_import(self.csv, self.db)
        self.write([('A', 'C', '120', 'issued'), ('A', 'C', '130', 'paid'), ('B', 'D', '1', 'paid')])
        self.assertEqual(self.run_import(self.csv, self.db), 2)
        expected = [('A', 'C', 130, 'paid'), ('B', 'D', 1, 'paid')]
        self.assertEqual(self.rows(), expected)
        self.assertEqual(self.run_import(self.csv, self.db), 2)
        self.assertEqual(self.rows(), expected)

    def test_constraint_invalid_file_atomic(self):
        self.write([('keep', 'old', '10', 'paid')])
        self.run_import(self.csv, self.db)
        before = self.rows()
        invalid = [('', 'C', '1', 'paid'), ('X', ' ', '1', 'paid'),
                   ('X', 'C', '-1', 'paid'), ('X', 'C', '1.5', 'paid'),
                   ('X', 'C', '1e3', 'paid'), ('X', 'C', '+1', 'paid'),
                   ('X', 'C', '١', 'paid'), ('X', 'C', str(2**63), 'paid'),
                   ('X', 'C', '1', 'unknown'), ('X', 'C', '1')]
        for bad in invalid:
            self.write([('new', 'C', '3', 'issued'), bad, ('X', 'C', '2', 'paid')])
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.run_import(self.csv, self.db)
            self.assertEqual(self.rows(), before, 'Partial import after invalid row')

    def test_constraint_missing_headers_atomic(self):
        self.write([('keep', 'C', '2', 'paid')])
        self.run_import(self.csv, self.db)
        before = self.rows()
        for header in [[], ['invoice_id', 'customer_id', 'amount_cents']]:
            self.write([], fields=header)
            with self.assertRaises(ValueError):
                self.run_import(self.csv, self.db)
            self.assertEqual(self.rows(), before)

    def test_empty_and_reordered_headers(self):
        self.write([])
        self.assertEqual(self.run_import(self.csv, self.db), 0)
        self.assertEqual(self.rows(), [])
        self.write([('paid', 'C', '0001', '7', 'ignored')],
                   fields=['status', 'customer_id', 'invoice_id', 'amount_cents', 'extra'])
        self.assertEqual(self.run_import(self.csv, self.db), 1)
        self.assertEqual(self.rows(), [('0001', 'C', 7, 'paid')])

    def test_constraint_sql_safe_identifiers(self):
        key = "invoice'); DROP TABLE invoices; --"
        self.write([(key, "O'Connor", '4', 'paid')])
        self.run_import(self.csv, self.db)
        self.assertEqual(self.rows(), [(key, "O'Connor", 4, 'paid')])

    def test_unrelated_rows_unchanged(self):
        self.write([('keep', 'C', '10', 'cancelled')])
        self.run_import(self.csv, self.db)
        self.write([('new', 'D', '20', 'paid')])
        self.run_import(self.csv, self.db)
        self.assertEqual(self.rows(), [('keep', 'C', 10, 'cancelled'), ('new', 'D', 20, 'paid')])

    def test_property_generated_batches(self):
        rng = random.Random(614)
        expected = {}
        for _ in range(8):
            batch = [(f'{rng.randrange(15):04}', f'C{rng.randrange(4)}',
                      str(rng.randrange(100000)), rng.choice(['issued', 'paid', 'cancelled']))
                     for _ in range(25)]
            for key, customer, cents, status in batch:
                expected[key] = (key, customer, int(cents), status)
            self.write(batch)
            self.assertEqual(self.run_import(self.csv, self.db), len({r[0] for r in batch}))
            self.assertEqual(self.rows(), sorted(expected.values()))



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'imported': 1, 'invoices': [['001', 'C01', 30, 'paid']]}})
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
