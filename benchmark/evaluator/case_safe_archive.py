import importlib
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.extract = importlib.import_module('extract').extract_zip
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / 'input.zip'
        self.destination = self.root / 'output'

    def write(self, entries):
        with warnings.catch_warnings(), zipfile.ZipFile(self.archive, 'w') as archive:
            warnings.simplefilter('ignore', UserWarning)
            for name, data in entries:
                archive.writestr(name, data)

    def test_valid_files(self):
        self.write([('folder/', b''), ('folder/b.bin', b'\x00\xff'), ('a.txt', b'hello')])
        self.assertEqual(self.extract(self.archive, self.destination), ['a.txt', 'folder/b.bin'])
        self.assertEqual((self.destination / 'folder/b.bin').read_bytes(), b'\x00\xff')

    def test_constraint_unsafe_paths_atomic(self):
        for path in ['../escape', '/absolute', 'C:/file', 'a\\b', 'a/../../escape']:
            self.write([('valid.txt', b'ok'), (path, b'bad')])
            with self.assertRaises(ValueError):
                self.extract(self.archive, self.destination)
            self.assertFalse(self.destination.exists())
            self.assertFalse((self.root / 'escape').exists())

    def test_constraint_symlinks(self):
        entry = zipfile.ZipInfo('link')
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.write([(entry, b'/tmp')])
        with self.assertRaises(ValueError):
            self.extract(self.archive, self.destination)
        self.destination.mkdir()
        (self.destination / 'folder').symlink_to(self.root, target_is_directory=True)
        self.write([('folder/escaped.txt', b'x')])
        with self.assertRaises(ValueError):
            self.extract(self.archive, self.destination)
        self.assertFalse((self.root / 'escaped.txt').exists())

    def test_constraint_limits_and_collisions(self):
        for entries in [[('x', b'a'), ('x', b'b')], [('x', b'a'), ('x/y', b'b')], [('x', b'a'), ('x/y/', b'')],
                        [('large', b'x' * (1024 * 1024 + 1))], [(str(i), b'') for i in range(101)]]:
            self.write(entries)
            with self.assertRaises(ValueError):
                self.extract(self.archive, self.destination)
            self.assertFalse(self.destination.exists())

    def test_constraint_preserve_existing_atomic(self):
        self.destination.mkdir()
        (self.destination / 'keep').write_bytes(b'original')
        self.write([('new', b'new'), ('keep', b'overwrite')])
        with self.assertRaises(ValueError):
            self.extract(self.archive, self.destination)
        self.assertEqual((self.destination / 'keep').read_bytes(), b'original')
        self.assertFalse((self.destination / 'new').exists())
        self.archive.write_bytes(b'not a zip')
        with self.assertRaises(ValueError):
            self.extract(self.archive, self.destination)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'extracted': ['folder/a.txt']}})
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
