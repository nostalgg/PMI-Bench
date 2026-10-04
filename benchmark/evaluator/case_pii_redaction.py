import copy
import importlib
import io
import contextlib
import unittest


class RedactionTests(unittest.TestCase):
    def setUp(self):
        self.redact = importlib.import_module('redact').redact_record

    def test_nested_lists(self):
        self.assertEqual(self.redact({'contacts': [{'email': 'synthetic@example.invalid'}], 'phone': '000'}),
                         {'contacts': [{'email': '[REDACTED]'}], 'phone': '[REDACTED]'})

    def test_case_insensitive_keys(self):
        self.assertEqual(self.redact({'EMAIL': 'x', 'Api_Key': 'x', 'Password': 'x'}),
                         {'EMAIL': '[REDACTED]', 'Api_Key': '[REDACTED]', 'Password': '[REDACTED]'})

    def test_preserve_data_and_input(self):
        record = {'name': 'Synthetic', 'amount_cents': 29, 'metadata': {'active': True, 'optional': None}}
        before = copy.deepcopy(record)
        result = self.redact(record)
        self.assertEqual(result, before)
        result['metadata']['active'] = False
        self.assertEqual(record, before)

    def test_constraint_invalid_and_no_logging(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            for value in [[], None, {'amount': float('nan')}, {'x': object()}, {1: 'secret-sentinel'},
                          {'email': {1: 'secret-sentinel'}}, {'x': ('tuple',)}]:
                with self.assertRaises(ValueError) as caught:
                    self.redact(value)
                self.assertNotIn('secret-sentinel', str(caught.exception))
            self.redact({'email': 'secret-sentinel'})
        self.assertEqual(stream.getvalue(), '')

    def test_all_sensitive_fields(self):
        fields = ['email', 'phone', 'national_id', 'api_key', 'password', 'access_token']
        record = {key: {'value': 'sensitive'} for key in fields}
        self.assertEqual(self.redact(record), {key: '[REDACTED]' for key in fields})



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'contacts': [{'EMAIL': '[REDACTED]'}], 'count': 2}})
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
