import copy
import importlib
import unittest


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.prepare=importlib.import_module('features').prepare_features
        self.rows=[{'id':'001','date':'2024-01-01','orders':2,'spend_cents':100,'target':10},
                   {'id':'002','date':'2024-01-02','orders':4,'spend_cents':300,'target':20},
                   {'id':'003','date':'2024-02-01','orders':1000,'spend_cents':99999,'target':None}]

    def test_cutoff_exclusive_training(self):
        result=self.prepare(self.rows,'2024-02-01')
        self.assertEqual([r['id'] for r in result['train']],['001','002'])
        self.assertEqual([r['id'] for r in result['test']],['003'])

    def test_medians_use_training_only(self):
        result=self.prepare(self.rows,'2024-02-01')
        self.assertEqual(result['medians'],{'orders':3,'spend_cents':200})

    def test_imputation_and_labels_not_features(self):
        self.rows[2]['orders']=None
        result=self.prepare(self.rows,'2024-02-01')
        self.assertEqual(result['test'][0],{'id':'003','features':{'orders':3,'spend_cents':99999},'target':None})
        self.assertEqual(set(result['train'][0]['features']),{'orders','spend_cents'})

    def test_order_and_input_preserved(self):
        before=copy.deepcopy(self.rows)
        result=self.prepare(list(reversed(self.rows)),'2024-02-01')
        self.assertEqual([r['id'] for r in result['train']],['001','002'])
        self.assertEqual(self.rows,before)

    def test_constraint_missing_training_observations(self):
        for rows in [[],[self.rows[2]],[{**self.rows[0],'orders':None}]]:
            with self.assertRaises(ValueError):
                self.prepare(rows,'2024-02-01')

    def test_constraint_invalid_or_duplicate_rows(self):
        for rows in [[self.rows[0],self.rows[0]],[{**self.rows[0],'date':'2024-02-30'}],
                     [{**self.rows[0],'target':None}],[{**self.rows[0],'orders':True}]]:
            with self.assertRaises(ValueError):
                self.prepare(rows,'2024-02-01')



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'train': [{'id': '001', 'features': {'orders': 2, 'spend_cents': 100}, 'target': 10}, {'id': '002', 'features': {'orders': 4, 'spend_cents': 300}, 'target': 20}], 'test': [{'id': '003', 'features': {'orders': 3.0, 'spend_cents': 99999}, 'target': None}], 'medians': {'orders': 3.0, 'spend_cents': 200.0}}})
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
