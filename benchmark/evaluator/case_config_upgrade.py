import copy
import importlib
import unittest


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.normalize = importlib.import_module('configuration').normalize_config
        self.v1 = {'schema_version': 1, 'endpoint': 'http://127.0.0.1:8000/v1', 'timeout_ms': 2500, 'model': 'local'}

    def test_timeout_units(self):
        result = self.normalize(self.v1)
        self.assertEqual(result, {'schema_version': 2, 'model': 'local',
                                 'connection': {'base_url': self.v1['endpoint'], 'timeout_seconds': 2.5}})

    def test_v2_preserved_without_aliases(self):
        v2 = {'schema_version': 2, 'model': 'custom',
              'connection': {'base_url': 'http://localhost:80/v1', 'timeout_seconds': 0.25}}
        original = copy.deepcopy(v2)
        result = self.normalize(v2)
        self.assertEqual(result, original)
        result['connection']['timeout_seconds'] = 99
        self.assertEqual(v2, original)

    def test_input_unchanged(self):
        original = copy.deepcopy(self.v1)
        self.normalize(self.v1)
        self.assertEqual(self.v1, original)

    def test_constraint_invalid_configuration(self):
        invalid = [None, {}, {**self.v1, 'extra': 1}, {**self.v1, 'schema_version': []},
                   {**self.v1, 'schema_version': True}, {**self.v1, 'schema_version': 3},
                   {**self.v1, 'timeout_ms': True}, {**self.v1, 'timeout_ms': 1.5},
                   {**self.v1, 'timeout_ms': 0}, {**self.v1, 'model': ' '},
                   {**self.v1, 'endpoint': ''}]
        for value in [float('nan'), float('inf'), -1, True]:
            invalid.append({'schema_version': 2, 'model': 'm', 'connection': {'base_url': 'x', 'timeout_seconds': value}})
        for config in invalid:
            before = copy.deepcopy(config)
            with self.assertRaises(ValueError):
                self.normalize(config)
            # NaN is not equal to itself; compare stable representations instead.
            self.assertEqual(repr(config), repr(before))

    def test_generated_timeouts(self):
        for ms in [1, 29, 999, 1000, 5001, 60000]:
            result = self.normalize({**self.v1, 'timeout_ms': ms})
            self.assertEqual(result['connection']['timeout_seconds'], ms / 1000)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'schema_version': 2, 'model': 'private', 'connection': {'base_url': 'http://127.0.0.1:8000/v1', 'timeout_seconds': 2.5}}})
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
