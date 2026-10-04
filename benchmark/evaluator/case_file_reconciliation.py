import importlib
import random
import unittest


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.reconcile = importlib.import_module('reconcile').reconcile

    def test_duplicates_are_events(self):
        self.assertEqual(self.reconcile(['A', 'A', 'B'], ['A', 'A', 'A']),
                         {'matched': 2, 'missing': ['B'], 'unexpected': ['A']})

    def test_sorted_string_identifiers(self):
        self.assertEqual(self.reconcile(['002', '001', '001'], ['1', '001']),
                         {'matched': 1, 'missing': ['001', '002'], 'unexpected': ['1']})

    def test_empty_and_identical(self):
        self.assertEqual(self.reconcile([], []), {'matched': 0, 'missing': [], 'unexpected': []})
        self.assertEqual(self.reconcile(['X', 'X'], ['X', 'X']), {'matched': 2, 'missing': [], 'unexpected': []})

    def test_constraint_invalid_ids_and_no_mutation(self):
        for invalid in [[''], [1], ['A', None], 'A', None]:
            with self.assertRaises(ValueError):
                self.reconcile(invalid, [])
            with self.assertRaises(ValueError):
                self.reconcile([], invalid)
        left, right = ['B', 'A'], ['A', 'B']
        self.reconcile(left, right)
        self.assertEqual(left, ['B', 'A'])
        self.assertEqual(right, ['A', 'B'])

    def test_generated_multisets(self):
        rng = random.Random(142)
        for _ in range(80):
            left = [rng.choice('ABC') for _ in range(rng.randrange(20))]
            right = [rng.choice('ABC') for _ in range(rng.randrange(20))]
            expected = {'matched': sum(min(left.count(k), right.count(k)) for k in 'ABC'),
                        'missing': [k for k in 'ABC' for _ in range(max(0, left.count(k)-right.count(k)))],
                        'unexpected': [k for k in 'ABC' for _ in range(max(0, right.count(k)-left.count(k)))]}
            self.assertEqual(self.reconcile(left, right), expected)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'matched': 2, 'missing': ['B'], 'unexpected': ['A']}})
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
