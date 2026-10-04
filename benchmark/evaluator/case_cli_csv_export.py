import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source,self.output=self.root/'incoming.csv',self.root/'report.jsonl'
        self.source.write_text('id,amount_cents\n001,29\n002,300\n')

    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-I','-B','/submission/tool.py',*map(str,args)],capture_output=True,text=True,timeout=5)

    def test_legacy_positional_contract(self):
        result=self.run_cli(self.source,self.output)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual([json.loads(x) for x in self.output.read_text().splitlines()],[{'id':'001','amount_cents':29},{'id':'002','amount_cents':300}])
        self.assertEqual(json.loads(result.stdout),{'rows':2,'dry_run':False})

    def test_named_paths(self):
        result=self.run_cli('--input',self.source,'--output',self.output)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(self.output.is_file())

    def test_dry_run_preserves_existing(self):
        self.output.write_text('keep')
        result=self.run_cli('--input',self.source,'--output',self.output,'--dry-run')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.output.read_text(),'keep')
        self.assertEqual(json.loads(result.stdout),{'rows':2,'dry_run':True})

    def test_constraint_invalid_row_preserves_output(self):
        self.output.write_text('keep')
        for bad in ['bad,-1','bad,1.2','bad,','bad,1,extra']:
            self.source.write_text('id,amount_cents\n001,29\n'+bad+'\n')
            result=self.run_cli(self.source,self.output)
            self.assertEqual(result.returncode,2)
            self.assertEqual(self.output.read_text(),'keep')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['incoming.csv','report.jsonl'])

    def test_constraint_mixed_arguments_rejected(self):
        result=self.run_cli(self.source,self.output,'--input',self.source)
        self.assertEqual(result.returncode,2)
        self.assertFalse(self.output.exists())

    def test_empty_input_and_large_integer(self):
        self.source.write_text('id,amount_cents\n')
        result=self.run_cli(self.source,self.output)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.output.read_text(),'')
        self.source.write_text(f'id,amount_cents\n001,{2**63-1}\n')
        result=self.run_cli(self.source,self.output)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(self.output.read_text())['amount_cents'],2**63-1)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'receipt': {'rows': 1, 'dry_run': False}, 'records': [{'id': '001', 'amount_cents': 29}]}})
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
