import importlib
import unittest
from support import connect_schema


def event(sequence,key='001',operation='upsert',value='new'):
    return {'sequence':sequence,'record_id':key,'operation':operation,'value':value}


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.apply=importlib.import_module('sync').apply_changes
        self.db=connect_schema(self)

    def rows(self):
        return self.db.execute('SELECT * FROM replica ORDER BY record_id').fetchall()

    def test_ordered_upserts_and_replays(self):
        self.assertEqual(self.apply(self.db,[event(2,value='last'),event(1,value='first')]),2)
        self.assertEqual(self.rows(),[('001','last')])
        self.assertEqual(self.apply(self.db,[event(2,value='last')]),0)

    def test_tombstone_removes_record(self):
        self.apply(self.db,[event(1),event(2,operation='delete',value=None)])
        self.assertEqual(self.rows(),[])
        self.assertEqual(self.db.execute('SELECT sequence FROM checkpoint').fetchone()[0],2)

    def test_constraint_checkpoint_atomic_on_db_failure(self):
        self.db.executescript("CREATE TRIGGER reject_bad BEFORE INSERT ON replica WHEN NEW.value='reject' BEGIN SELECT RAISE(ABORT,'synthetic rejection'); END;")
        before=list(self.db.iterdump())
        with self.assertRaises(Exception):
            self.apply(self.db,[event(1),event(2,key='bad',value='reject')])
        self.assertEqual(list(self.db.iterdump()),before)

    def test_constraint_bad_or_conflicting_batch(self):
        for rows in [[event(1),event(1,value='different')],[event(1),event(2,operation='delete',value='x')],
                      [event(True)], [event(0)]]:
            before=list(self.db.iterdump())
            with self.assertRaises(ValueError):
                self.apply(self.db,rows)
            self.assertEqual(list(self.db.iterdump()),before)

    def test_duplicates_and_empty_batch(self):
        self.assertEqual(self.apply(self.db,[event(1),event(1)]),1)
        self.assertEqual(self.apply(self.db,[]),0)
        self.assertEqual(self.rows(),[('001','new')])

    def test_constraint_caller_transaction(self):
        self.db.execute('UPDATE checkpoint SET sequence=1')
        with self.assertRaises(ValueError):
            self.apply(self.db,[])
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
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'applied': 2, 'checkpoint': 2, 'records': []}})
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
