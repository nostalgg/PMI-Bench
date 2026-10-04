import importlib
import random
import unittest


class MoneyTests(unittest.TestCase):
    def setUp(self):
        self.parse = importlib.import_module('money').parse_amount

    def test_decimal_cents(self):
        for text, expected in [('0', 0), (' 12,3 ', 1230), ('0,29', 29), ('12,99', 1299)]:
            self.assertEqual(self.parse(text), expected)

    def test_grouping_and_refunds(self):
        for text, expected in [('1.234,56', 123456), ('-12.345,01', -1234501), ('-0,01', -1)]:
            self.assertEqual(self.parse(text), expected)

    def test_exact_large_amount(self):
        self.assertEqual(self.parse('90071992547409,91'), 9007199254740991)
        self.assertEqual(self.parse('92233720368547758,07'), 2**63 - 1)
        self.assertEqual(self.parse('-92233720368547758,08'), -(2**63))

    def test_constraint_invalid_amount(self):
        for text in ['', '1.23', '1,234', '1e3', '+1', '1 000', '€1', '١', '--1',
                     '92233720368547758,08', '-92233720368547758,09', None, 1]:
            with self.assertRaises(ValueError, msg=repr(text)):
                self.parse(text)

    def test_generated_amounts(self):
        rng = random.Random(120)
        for _ in range(150):
            cents = rng.randrange(-10**12, 10**12)
            whole, fraction = divmod(abs(cents), 100)
            text = f'{whole:,}'.replace(',', '.') + f',{fraction:02}'
            self.assertEqual(self.parse(('-' if cents < 0 else '') + text), cents)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'total_cents': 123427}})
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
