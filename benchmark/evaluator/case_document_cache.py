import contextlib
import importlib
import io
import traceback
import unittest
from support import connect_schema


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.enrich=importlib.import_module('enrichment').enrich_documents
        self.db=connect_schema(self)
        self.records=[{'record_id':'001','text':'Synthetic invoice'},{'record_id':'002','text':'Synthetic credit'}]
        self.calls=[]

    def classify(self,rows):
        self.calls.append(rows)
        return {'model':'local','results':[{'record_id':r['record_id'],'label':'invoice' if r['record_id']=='001' else 'credit_note'} for r in reversed(rows)]}

    def test_cache_replay_avoids_model_calls(self):
        self.assertEqual(self.enrich(self.db,self.records,self.classify,'local'),2)
        self.assertEqual(self.enrich(self.db,self.records,self.classify,'local'),0)
        self.assertEqual(len(self.calls),1)

    def test_changed_content_or_model_invalidates_cache(self):
        self.enrich(self.db,self.records,self.classify,'local')
        self.assertEqual(self.enrich(self.db,[{**self.records[0],'text':'Changed'}],self.classify,'local'),1)
        def alternate(rows):
            return {'model':'new-model','results':[{'record_id':r['record_id'],'label':'other'} for r in rows]}
        self.assertEqual(self.enrich(self.db,self.records,alternate,'new-model'),2)

    def test_alignment_by_id_not_response_order(self):
        self.enrich(self.db,self.records,self.classify,'local')
        self.assertEqual(self.db.execute('SELECT record_id,label FROM enrichment ORDER BY record_id').fetchall(),[('001','invoice'),('002','credit_note')])

    def test_constraint_invalid_response_atomic(self):
        for response in [None,{'model':'wrong','results':[]}, {'model':'local','results':[{'record_id':'001','label':'invoice'}]},
                         {'model':'local','results':[{'record_id':'001','label':'invoice'}]*2},
                         {'model':'local','results':[{'record_id':'001','label':'invented'},{'record_id':'002','label':'invoice'}]}]:
            with self.assertRaises(ValueError):
                self.enrich(self.db,self.records,lambda _:response,'local')
            self.assertEqual(self.db.execute('SELECT count(*) FROM enrichment').fetchone()[0],0)

    def test_constraint_callback_error_is_sanitized(self):
        def fail(_):
            raise RuntimeError('sensitive-sentinel')
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
            try:
                self.enrich(self.db,self.records,fail,'local')
            except RuntimeError:
                traceback.print_exc()
            else:
                self.fail('Expected a sanitized failure')
        self.assertNotIn('sensitive-sentinel',stream.getvalue())
        self.assertEqual(self.db.execute('SELECT count(*) FROM enrichment').fetchone()[0],0)

    def test_constraint_db_failure_or_conflicting_input_atomic(self):
        self.db.executescript("CREATE TRIGGER reject_second BEFORE INSERT ON enrichment WHEN NEW.record_id='002' BEGIN SELECT RAISE(ABORT,'synthetic rejection'); END;")
        with self.assertRaises(Exception):
            self.enrich(self.db,self.records,self.classify,'local')
        self.assertEqual(self.db.execute('SELECT count(*) FROM enrichment').fetchone()[0],0)
        self.calls.clear()
        with self.assertRaises(ValueError):
            self.enrich(self.db,[self.records[0],{**self.records[0],'text':'conflict'}],self.classify,'local')
        self.assertEqual(self.calls,[])



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'enriched': 2, 'labels': [['001', 'invoice'], ['002', 'credit_note']]}})
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
