import copy
import importlib
import unittest


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.match=importlib.import_module('matching').match_customers

    def test_normalized_email(self):
        self.assertEqual(self.match([{'customer_id':'001','email':'  USER@EXAMPLE.INVALID '}],
                                   [{'source_id':'s1','email':'user@example.invalid'}]),
                         {'matches':[{'source_id':'s1','customer_id':'001'}],'unresolved':[]})

    def test_ambiguous_not_arbitrarily_assigned(self):
        master=[{'customer_id':'B','email':'shared@example.invalid'}, {'customer_id':'A','email':'SHARED@example.invalid'}]
        result=self.match(master,[{'source_id':'x','email':'shared@example.invalid'}])
        self.assertEqual(result,{'matches':[],'unresolved':[{'source_id':'x','reason':'ambiguous','candidates':['A','B']}]})

    def test_empty_email_never_matches(self):
        result=self.match([{'customer_id':'001','email':''}],[{'source_id':'s','email':' '}])
        self.assertEqual(result['unresolved'],[{'source_id':'s','reason':'not_found','candidates':[]}])

    def test_source_order_and_no_mutation(self):
        master=[{'customer_id':'001','email':'a@b.invalid'}]
        incoming=[{'source_id':'s2','email':'a@b.invalid'},{'source_id':'s1','email':'a@b.invalid'}]
        before=copy.deepcopy((master,incoming))
        result=self.match(master,incoming)
        self.assertEqual([r['source_id'] for r in result['matches']],['s2','s1'])
        self.assertEqual((master,incoming),before)

    def test_constraint_duplicate_identifiers(self):
        for master,incoming in [([{'customer_id':'A','email':'x'}]*2,[]),
                                 ([],[{'source_id':'A','email':'x'}]*2)]:
            with self.assertRaises(ValueError):
                self.match(master,incoming)

    def test_constraint_invalid_rows(self):
        for master,incoming in [(None,[]),([],{}),([{'customer_id':1,'email':'x'}],[]),
                                ([],[{'source_id':'s','email':None}])]:
            with self.assertRaises(ValueError):
                self.match(master,incoming)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'matches': [], 'unresolved': [{'source_id': 'CRM-8', 'reason': 'ambiguous', 'candidates': ['001', '002']}]}})
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
