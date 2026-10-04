import copy
import importlib
import unittest
from vendor_v2 import Page


class Legacy:
    api_version = 1

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def list_records(self, *, page):
        self.calls.append(page)
        return {'items': self.pages[page-1], 'has_more': page < len(self.pages)}


class Modern:
    api_version = 2

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def fetch_page(self, *, cursor):
        self.calls.append(cursor)
        index = 0 if cursor is None else int(cursor)
        return Page(self.pages[index], str(index+1) if index+1 < len(self.pages) else None)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.collect = importlib.import_module('adapter').collect_records

    def test_legacy_pagination(self):
        client = Legacy([[{'id': '001'}], [{'id': '002'}]])
        self.assertEqual(self.collect(client), [{'id': '001'}, {'id': '002'}])
        self.assertEqual(client.calls, [1, 2])

    def test_modern_empty_intermediate_page(self):
        client = Modern([[1], [], [2]])
        self.assertEqual(self.collect(client), [1, 2])
        self.assertEqual(client.calls, [None, '1', '2'])

    def test_duplicates_and_order_preserved(self):
        self.assertEqual(self.collect(Modern([[2, 2], [1, 2]])), [2, 2, 1, 2])

    def test_constraint_pagination_bounds(self):
        for limit in [0, -1, True, 1.2]:
            with self.assertRaises(ValueError):
                self.collect(Legacy([[]]), max_pages=limit)
        with self.assertRaises(ValueError):
            self.collect(Legacy([[1], [2]]), max_pages=1)
        class Loop:
            api_version = 2
            def fetch_page(self, *, cursor):
                return Page([1], 'same')
        with self.assertRaises(ValueError):
            self.collect(Loop(), max_pages=5)
        unknown = Legacy([[]])
        unknown.api_version = 3
        with self.assertRaises(ValueError):
            self.collect(unknown)

    def test_input_pages_unchanged(self):
        pages = [[{'id': '001'}], []]
        before = copy.deepcopy(pages)
        self.collect(Modern(pages))
        self.assertEqual(pages, before)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'records': [1, 2, 2]}})
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
