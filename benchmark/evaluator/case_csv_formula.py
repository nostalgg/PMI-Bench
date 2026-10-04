import copy
import csv
import importlib
import io
import unittest


class SpreadsheetTests(unittest.TestCase):
    def setUp(self):
        self.export=importlib.import_module('contacts').export_contacts
        self.row={'customer_id':'001','name':'Synthetic','email':'x@example.invalid','notes':'note'}

    def parse(self,records):
        return list(csv.reader(io.StringIO(self.export(records))))

    def test_constraint_formula_prefixes(self):
        for value in ['=1+1','+SUM(A1:A2)','-1+1','@SUM(1,2)']:
            self.assertEqual(self.parse([{key:value for key in self.row}])[1],["'"+value]*4)

    def test_constraint_whitespace_and_control_prefixes(self):
        for value in ['   =1','\ttext','\rtext','\ntext',' \t@SUM(1)']:
            self.assertEqual(self.parse([{**self.row,'notes':value}])[1][3],"'"+value)

    def test_plain_cells_preserved(self):
        self.assertEqual(self.parse([self.row]),[['customer_id','name','email','notes'],list(self.row.values())])

    def test_quotes_newlines_and_existing_apostrophe(self):
        value="'safe, \"quoted\"\ntext"
        self.assertEqual(self.parse([{**self.row,'notes':value}])[1][3],value)

    def test_input_unchanged(self):
        records=[{**self.row,'notes':'=danger'}]
        before=copy.deepcopy(records)
        self.export(records)
        self.assertEqual(records,before)

    def test_constraint_invalid_records(self):
        for value in [None,[{**self.row,'notes':1}],[{'name':'only'}]]:
            with self.assertRaises(ValueError):
                self.export(value)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'rows': [['customer_id', 'name', 'email', 'notes'], ['001', 'Synthetic', 'x@example.invalid', "'=1+1"]]}})
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
