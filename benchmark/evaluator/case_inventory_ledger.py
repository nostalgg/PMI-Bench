import importlib
import unittest
from support import connect_schema


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.apply=importlib.import_module('ledger').apply_movements
        self.db=connect_schema(self)
        self.db.execute("INSERT INTO stock VALUES('001',10)")
        self.db.commit()
        self.event={'event_id':'delivery-1','sku':'001','delta':5}

    def test_apply_and_replay(self):
        self.assertEqual(self.apply(self.db,[self.event]),1)
        self.assertEqual(self.apply(self.db,[self.event,self.event]),0)
        self.assertEqual(self.db.execute('SELECT quantity FROM stock').fetchone()[0],15)

    def test_batch_duplicates_once(self):
        self.assertEqual(self.apply(self.db,[self.event,self.event]),1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM movements').fetchone()[0],1)

    def test_negative_stock_and_unrelated_sku(self):
        self.db.execute("INSERT INTO stock VALUES('other',7)")
        self.db.commit()
        self.apply(self.db,[{**self.event,'delta':-12}])
        self.assertEqual(self.db.execute('SELECT * FROM stock ORDER BY sku').fetchall(),[('001',-2),('other',7)])

    def test_constraint_conflicting_replay_atomic(self):
        self.apply(self.db,[self.event])
        before=list(self.db.iterdump())
        with self.assertRaises(ValueError):
            self.apply(self.db,[{**self.event,'event_id':'new'}, {**self.event,'delta':6}])
        self.assertEqual(list(self.db.iterdump()),before)

    def test_constraint_unknown_sku_and_invalid_values(self):
        for bad in [{**self.event,'sku':'missing'}, {**self.event,'delta':True}, {**self.event,'delta':0},
                    {**self.event,'event_id':''}, {**self.event,'delta':10**6+1}]:
            before=list(self.db.iterdump())
            with self.assertRaises(ValueError):
                self.apply(self.db,[self.event,bad])
            self.assertEqual(list(self.db.iterdump()),before)

    def test_constraint_caller_transaction(self):
        self.db.execute("UPDATE stock SET quantity=3")
        with self.assertRaises(ValueError):
            self.apply(self.db,[])
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'applied': 1, 'stock': [['001', 15], ['002', 7]]}})
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
