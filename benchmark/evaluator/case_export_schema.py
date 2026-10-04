import copy
import csv
import importlib
import io
import unittest


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.render=importlib.import_module('exporter').render_export
        self.row={'invoice_id':'001','amount_cents':29,'currency':'EUR','status':'issued'}

    def parse(self,rows,version):
        return list(csv.reader(io.StringIO(self.render(rows,version))))

    def test_legacy_header_and_decimal(self):
        self.assertEqual(self.parse([self.row],1),[['invoice_id','amount_eur','status'],['001','0.29','issued']])

    def test_current_header_and_currency(self):
        self.assertEqual(self.parse([{**self.row,'currency':'USD'}],2),[['invoice_id','amount_cents','currency','status'],['001','29','USD','issued']])

    def test_exact_large_and_negative_amounts(self):
        rows=[{**self.row,'amount_cents':9007199254740991},{**self.row,'invoice_id':'N','amount_cents':-1}]
        self.assertEqual(self.parse(rows,1)[1:], [['001','90071992547409.91','issued'],['N','-0.01','issued']])

    def test_csv_quoting_and_no_input_mutation(self):
        rows=[{**self.row,'invoice_id':'a,"b\nc'}]
        before=copy.deepcopy(rows)
        self.assertEqual(self.parse(rows,2)[1][0],rows[0]['invoice_id'])
        self.assertEqual(rows,before)

    def test_constraint_reject_unsupported_legacy_currency(self):
        with self.assertRaises(ValueError):
            self.render([{**self.row,'currency':'USD'}],1)

    def test_constraint_bad_versions_and_rows(self):
        for version in [0,3,True,[]]:
            with self.assertRaises(ValueError):
                self.render([],version)
        for row in [{**self.row,'amount_cents':True},{**self.row,'amount_cents':2**63},{**self.row,'status':'bad'}]:
            with self.assertRaises(ValueError):
                self.render([row],2)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'rows': [['invoice_id', 'amount_eur', 'status'], ['001', '0.29', 'issued']]}})
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
