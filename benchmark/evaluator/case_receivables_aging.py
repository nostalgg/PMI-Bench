from datetime import date,timedelta
import random
import sqlite3
import unittest
from pathlib import Path
from support import connect_schema


class AgingTests(unittest.TestCase):
    def setUp(self):
        self.db=connect_schema(self)
        self.sql=Path('/submission/aging.sql').read_text()
        self.db.executescript("INSERT INTO customers VALUES('001'),('002'); INSERT INTO report_config VALUES('2024-03-31');")

    def query(self):
        allowed={sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION}
        self.db.set_authorizer(lambda action,*_:sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
        try:
            cursor=self.db.execute(self.sql)
            self.assertEqual([c[0] for c in cursor.description],['customer_id','not_due_cents','days_1_30_cents','days_31_60_cents','days_61_plus_cents'])
            rows=cursor.fetchall()
            self.assertTrue(all(isinstance(x,int) for row in rows for x in row[1:]))
            return rows
        finally:
            self.db.set_authorizer(None)

    def invoice(self,key='I',due='2024-03-01',amount=1000,status='issued',issued='2024-01-01'):
        self.db.execute('INSERT INTO invoices VALUES(?,?,?,?,?,?)',(key,'001',amount,issued,due,status))

    def payment(self,key,invoice='I',amount=100,day='2024-03-01',status='posted'):
        self.db.execute('INSERT INTO payments VALUES(?,?,?,?,?)',(key,invoice,amount,day,status))

    def test_partial_payments_and_cutoff(self):
        self.invoice()
        self.payment('P1',amount=100)
        self.payment('P2',amount=200)
        self.payment('future',amount=500,day='2024-04-01')
        self.payment('void',amount=100,status='void')
        self.assertEqual(self.query(),[('001',0,700,0,0),('002',0,0,0,0)])

    def test_bucket_boundaries(self):
        as_of=date(2024,3,31)
        for late in [-1,0,1,30,31,60,61]:
            self.invoice(str(late),(as_of-timedelta(days=late)).isoformat(),100)
        self.assertEqual(self.query()[0],('001',200,200,200,100))

    def test_paid_overpaid_void_and_future_invoices(self):
        self.invoice()
        self.payment('over',amount=1200)
        self.invoice('void',status='void')
        self.invoice('future',issued='2024-04-01')
        self.assertEqual(self.query()[0],('001',0,0,0,0))

    def test_customers_without_invoices(self):
        self.assertEqual(self.query(),[('001',0,0,0,0),('002',0,0,0,0)])

    def test_generated_against_python_oracle(self):
        rng=random.Random(194)
        expected=[0,0,0,0]
        as_of=date(2024,3,31)
        for i in range(40):
            late=rng.randrange(-10,100)
            amount=rng.randrange(100,2000)
            paid=[rng.randrange(300) for _ in range(rng.randrange(4))]
            self.invoice(str(i),(as_of-timedelta(days=late)).isoformat(),amount)
            for j,value in enumerate(paid):
                self.payment(f'{i}-{j}',str(i),value)
            index=0 if late<=0 else 1 if late<=30 else 2 if late<=60 else 3
            expected[index]+=max(amount-sum(paid),0)
        self.assertEqual(self.query()[0],('001',*expected))

    def test_constraint_read_only(self):
        self.invoice()
        before=list(self.db.iterdump())
        self.query()
        self.assertEqual(list(self.db.iterdump()),before)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'rows': [['001', 0, 7000, 0, 0], ['002', 0, 0, 0, 0]]}})
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
