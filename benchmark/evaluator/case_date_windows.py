import importlib
import unittest


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.day = importlib.import_module('windows').reporting_day

    def test_local_midnight(self):
        self.assertEqual(self.day('2024-01-01T23:30:00Z', 'Europe/Rome'), '2024-01-02')

    def test_previous_day(self):
        self.assertEqual(self.day('2024-07-01T02:00:00+00:00', 'America/New_York'), '2024-06-30')

    def test_daylight_saving_offsets(self):
        self.assertEqual(self.day('2024-03-30T22:30:00Z', 'Europe/Rome'), '2024-03-30')
        self.assertEqual(self.day('2024-03-31T22:30:00Z', 'Europe/Rome'), '2024-04-01')
        self.assertEqual(self.day('2024-10-27T22:30:00Z', 'Europe/Rome'), '2024-10-27')

    def test_constraint_invalid_timestamp(self):
        for stamp, zone in [('2024-01-01T12:00:00', 'UTC'), ('bad', 'UTC'),
                            ('2024-01-01T00:00:00Z', 'Invalid/Zone'), (None, 'UTC')]:
            with self.assertRaises(ValueError):
                self.day(stamp, zone)

    def test_equivalent_instants(self):
        stamps = ['2024-01-01T23:30:00Z', '2024-01-02T00:30:00+01:00', '2024-01-01T18:30:00-05:00']
        for stamp in stamps:
            self.assertEqual(self.day(stamp, 'Europe/Rome'), '2024-01-02')



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'reporting_date': '2024-01-02'}})
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
