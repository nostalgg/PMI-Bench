import copy
import importlib
import unittest


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.choose=importlib.import_module('routing').choose_model
        self.request={'data_class':'public','input_tokens':1000,'output_tokens':1000,'task':'sql','allow_hosted':True}
        self.local={'name':'local','deployment':'local','tasks':['sql','migration'],'context_tokens':10000,'input_per_million':'1','output_per_million':'2'}
        self.hosted={**self.local,'name':'hosted','deployment':'hosted','tasks':['sql'],'input_per_million':'0.1','output_per_million':'0.2'}
        self.policy={'budget_usd':'0.01','models':[self.local,self.hosted]}

    def test_lowest_eligible_cost(self):
        result=self.choose(self.request,self.policy)
        self.assertEqual(result['model'],'hosted')
        self.assertEqual(__import__('decimal').Decimal(result['estimated_cost_usd']),__import__('decimal').Decimal('0.0003'))

    def test_constraint_restricted_data_stays_local(self):
        self.assertEqual(self.choose({**self.request,'data_class':'restricted'},self.policy)['model'],'local')
        self.assertEqual(self.choose({**self.request,'allow_hosted':False},self.policy)['model'],'local')

    def test_capability_and_context(self):
        self.assertEqual(self.choose({**self.request,'task':'migration'},self.policy)['model'],'local')
        short={**self.hosted,'context_tokens':100}
        self.assertEqual(self.choose(self.request,{**self.policy,'models':[self.local,short]})['model'],'local')

    def test_constraint_budget_exact_and_no_eligible_model(self):
        local_only={**self.policy,'models':[self.local],'budget_usd':'0.003'}
        self.assertEqual(self.choose(self.request,local_only)['model'],'local')
        with self.assertRaises(ValueError):
            self.choose(self.request,{**local_only,'budget_usd':'0.002999'})
        with self.assertRaises(ValueError):
            self.choose({**self.request,'data_class':'restricted'},{**self.policy,'models':[self.hosted]})

    def test_tie_break_and_no_input_mutation(self):
        policy={**self.policy,'models':[self.local,{**self.local,'name':'a-local'}]}
        before=copy.deepcopy((self.request,policy))
        self.assertEqual(self.choose(self.request,policy)['model'],'a-local')
        self.assertEqual((self.request,policy),before)

    def test_constraint_invalid_configuration(self):
        for request,policy in [({**self.request,'input_tokens':True},self.policy),
            (self.request,{**self.policy,'budget_usd':'NaN'}),(self.request,{**self.policy,'models':[self.local,self.local]}),
            (self.request,{**self.policy,'models':[{**self.local,'input_per_million':'-1'}]})]:
            with self.assertRaises(ValueError):
                self.choose(request,policy)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'model': 'private', 'estimated_cost_usd': '0.003'}})
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
