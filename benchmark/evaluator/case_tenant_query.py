import importlib
import unittest
from support import connect_schema


class TenantTests(unittest.TestCase):
    def setUp(self):
        self.list_orders=importlib.import_module('queries').list_orders
        self.db=connect_schema(self)
        self.db.executemany('INSERT INTO orders VALUES(?,?,?,?)',[
            ('A','001',300,'2024-01-01'),('A','002',100,'2024-01-01'),('B','001',999,'2024-01-01')])
        self.db.commit()

    def test_tenant_isolation(self):
        self.assertEqual(self.list_orders(self.db,'A'),[('001',300,'2024-01-01'),('002',100,'2024-01-01')])
        self.assertEqual(self.list_orders(self.db,'B'),[('001',999,'2024-01-01')])

    def test_safe_sort_and_tie_break(self):
        self.assertEqual([r[0] for r in self.list_orders(self.db,'A','amount_cents','asc')],['002','001'])
        self.assertEqual([r[0] for r in self.list_orders(self.db,'A','amount_cents','desc')],['001','002'])

    def test_constraint_bound_tenant_value(self):
        self.assertEqual(self.list_orders(self.db,"A' OR 1=1 --"),[])

    def test_constraint_invalid_sort_rejected_before_query(self):
        queries=[]
        self.db.set_trace_callback(queries.append)
        for sort,direction in [('amount_cents; DROP TABLE orders','asc'),('unknown','asc'),('created_at','DESC; --')]:
            with self.assertRaises(ValueError):
                self.list_orders(self.db,'A',sort,direction)
        self.assertEqual(queries,[])

    def test_constraint_nonempty_tenant(self):
        for tenant in ['',None,True]:
            with self.assertRaises(ValueError):
                self.list_orders(self.db,tenant)

    def test_read_only_and_missing_tenant(self):
        before=list(self.db.iterdump())
        self.assertEqual(self.list_orders(self.db,'missing'),[])
        self.list_orders(self.db,'A')
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
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'orders': [['001', 300, '2024-01-01']]}})
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
