import csv
import importlib
import tempfile
import unittest
from pathlib import Path


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.publish=importlib.import_module('publish').publish_report
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.output=self.root/'report.csv'
        self.rows=[{'customer_id':'002','amount_cents':20},{'customer_id':'001','amount_cents':29},{'customer_id':'001','amount_cents':1}]

    def read(self):
        with self.output.open(newline='') as stream:
            return list(csv.reader(stream))

    def test_aggregates_and_order(self):
        self.assertEqual(self.publish(self.rows,self.output),2)
        self.assertEqual(self.read(),[['customer_id','amount_cents'],['001','30'],['002','20']])

    def test_replace_and_cleanup(self):
        self.output.write_text('previous report')
        self.publish(self.rows,self.output)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['report.csv'])
        self.assertNotIn('previous',self.output.read_text())
        directory=self.root/'not_a_file'
        directory.mkdir()
        (directory/'keep').write_text('original')
        with self.assertRaises(OSError):
            self.publish(self.rows,directory)
        self.assertEqual((directory/'keep').read_text(),'original')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['not_a_file','report.csv'])

    def test_constraint_invalid_late_row_preserves_report(self):
        self.output.write_text('previous report')
        with self.assertRaises(ValueError):
            self.publish(self.rows+[{'customer_id':'bad','amount_cents':True}],self.output)
        self.assertEqual(self.output.read_text(),'previous report')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['report.csv'])

    def test_constraint_overflow_preserves_report(self):
        self.output.write_text('previous report')
        with self.assertRaises(ValueError):
            self.publish([{'customer_id':'001','amount_cents':2**63-1},{'customer_id':'001','amount_cents':1}],self.output)
        self.assertEqual(self.output.read_text(),'previous report')

    def test_constraint_symlink_target_preserved(self):
        original=self.root/'protected.txt'
        original.write_text('keep')
        self.output.symlink_to(original)
        with self.assertRaises(ValueError):
            self.publish(self.rows,self.output)
        self.assertEqual(original.read_text(),'keep')
        self.assertTrue(self.output.is_symlink())

    def test_empty_and_quoted_identifiers(self):
        self.assertEqual(self.publish([],self.output),0)
        self.assertEqual(self.read(),[['customer_id','amount_cents']])
        self.publish([{'customer_id':'a,b','amount_cents':-29}],self.output)
        self.assertEqual(self.read()[1],['a,b','-29'])



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'customers': 1, 'rows': [['customer_id', 'amount_cents'], ['001', '30']]}})
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
