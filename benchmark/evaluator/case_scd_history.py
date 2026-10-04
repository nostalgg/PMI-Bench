import importlib
import unittest
from support import connect_schema


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.apply=importlib.import_module('history').apply_snapshot
        self.db=connect_schema(self)
        self.db.execute("INSERT INTO customer_history VALUES('001','Original','2024-01-01',NULL)")
        self.db.commit()

    def rows(self):
        return self.db.execute('SELECT * FROM customer_history ORDER BY customer_id,valid_from').fetchall()

    def test_changed_version_preserves_history(self):
        self.assertEqual(self.apply(self.db,[{'customer_id':'001','name':'New'}],'2024-02-01'),1)
        self.assertEqual(self.rows(),[('001','Original','2024-01-01','2024-02-01'),('001','New','2024-02-01',None)])

    def test_repeat_snapshot_unchanged(self):
        rows=[{'customer_id':'001','name':'Original'}]
        self.assertEqual(self.apply(self.db,rows,'2024-02-01'),0)
        self.assertEqual(self.apply(self.db,rows,'2024-02-01'),0)
        self.assertEqual(len(self.rows()),1)

    def test_missing_customer_closes_version(self):
        self.assertEqual(self.apply(self.db,[],'2024-02-01'),1)
        self.assertEqual(self.rows(),[('001','Original','2024-01-01','2024-02-01')])
        self.assertEqual(self.apply(self.db,[],'2024-02-01'),0)

    def test_add_and_reactivate_customer(self):
        self.apply(self.db,[],'2024-02-01')
        self.apply(self.db,[{'customer_id':'001','name':'Again'},{'customer_id':'002','name':'Second'}],'2024-03-01')
        self.assertEqual(self.rows(),[('001','Original','2024-01-01','2024-02-01'),('001','Again','2024-03-01',None),('002','Second','2024-03-01',None)])

    def test_constraint_late_or_same_day_change_atomic(self):
        for day in ['2023-12-31','2024-01-01']:
            before=self.rows()
            with self.assertRaises(ValueError):
                self.apply(self.db,[{'customer_id':'001','name':'Changed'}],day)
            self.assertEqual(self.rows(),before)

    def test_constraint_invalid_snapshot_or_active_transaction(self):
        for rows,day in [([{'customer_id':'001','name':'X'}]*2,'2024-02-01'),([], '2024-02-30')]:
            with self.assertRaises(ValueError):
                self.apply(self.db,rows,day)
        self.db.execute("UPDATE customer_history SET name='Pending'")
        with self.assertRaises(ValueError):
            self.apply(self.db,[],'2024-02-01')
        self.assertTrue(self.db.in_transaction)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'changed': 1, 'history': [['001', 'Original workshop', '2024-01-01', '2024-02-01'], ['001', 'Renamed workshop', '2024-02-01', None]]}})
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
