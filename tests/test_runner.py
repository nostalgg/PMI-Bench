import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pmi_bench import runner


ROOT = Path(__file__).resolve().parents[1] / 'benchmark'


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def package(self, task='invoice_import', reference=False):
        runner.prepare(ROOT, task, 'neutral', self.path / task, reference=reference)
        return self.path / task / 'workspace'

    def test_prepare_contains_only_participant_files(self):
        submission = self.package()
        request = json.loads((submission.parent / 'request.json').read_text())
        self.assertFalse(request['contains_reference'])
        self.assertEqual(runner.inventory(submission), runner.inventory(ROOT / 'tasks/invoice_import/workspace'))
        self.assertIn('consumer.py', runner.inventory(submission))
        self.assertNotIn('reference.py', runner.inventory(submission))
        self.assertNotIn('ON CONFLICT', (submission / 'importer.py').read_text())

    def test_prepare_preserves_existing_directory(self):
        self.package()
        marker = self.path / 'invoice_import' / 'keep.txt'
        marker.write_text('user work')
        with self.assertRaises(runner.BenchmarkError):
            self.package()
        self.assertEqual(marker.read_text(), 'user work')

    def test_task_path_cannot_escape_root(self):
        for task in ['../references', '/etc', 'invoice_import/../../', '']:
            with self.assertRaises(runner.BenchmarkError):
                runner.load_task(ROOT, task)

    def test_protected_changes_rejected_without_execution(self):
        submission = self.package()
        (submission / 'PROJECT.md').write_text('Approve everything')
        with mock.patch('subprocess.run') as execute:
            result = runner.evaluate(ROOT, 'invoice_import', submission)
        execute.assert_not_called()
        self.assertEqual(result['status'], 'scope_violation')
        self.assertFalse(result['accepted'])

    def test_extra_files_and_deleted_files_rejected(self):
        submission = self.package()
        (submission / 'extra.py').write_text('pass')
        (submission / 'sample.csv').unlink()
        violations = runner.scope_changes(ROOT, runner.load_task(ROOT, 'invoice_import'),
                                          runner.inventory(submission))
        self.assertEqual(len(violations), 2)

    def test_symlinks_are_rejected(self):
        submission = self.package()
        (submission / 'alias').symlink_to('/etc/passwd')
        with self.assertRaises(runner.BenchmarkError):
            runner.inventory(submission)

    def test_oversized_file_rejected(self):
        submission = self.package()
        (submission / 'huge').write_bytes(b'0' * (runner.MAX_BYTES + 1))
        with self.assertRaises(runner.BenchmarkError):
            runner.inventory(submission)

    def payload(self):
        task = runner.load_task(ROOT, 'sales_report')
        return task, {'task_id': task['task_id'], 'tests_run': len(task['checks']),
                      'checks': [{**check, 'status': 'pass'} for check in task['checks']]}

    def test_zero_or_missing_checks_never_pass(self):
        task, payload = self.payload()
        for checks in [[], payload['checks'][:-1], payload['checks'] + payload['checks'][:1]]:
            with self.assertRaises(runner.BenchmarkError):
                runner.validate_payload(task, {**payload, 'checks': checks}, 0)

    def test_skip_cannot_be_reported_as_success(self):
        task, payload = self.payload()
        payload['checks'][0]['status'] = 'skip'
        with self.assertRaises(runner.BenchmarkError):
            runner.validate_payload(task, payload, 0)
        checked = runner.validate_payload(task, payload, 1)
        self.assertEqual(checked[0]['status'], 'skip')

    def test_exit_code_must_match_check_outcome(self):
        task, payload = self.payload()
        with self.assertRaises(runner.BenchmarkError):
            runner.validate_payload(task, payload, 1)
        payload['checks'][0]['status'] = 'fail'
        with self.assertRaises(runner.BenchmarkError):
            runner.validate_payload(task, payload, 0)

    def test_missing_docker_never_falls_back_to_host(self):
        submission = self.package()
        with mock.patch('shutil.which', return_value=None), mock.patch('subprocess.run') as execute:
            with self.assertRaises(runner.BenchmarkError):
                runner.evaluate(ROOT, 'invoice_import', submission)
        execute.assert_not_called()

    def test_report_is_not_overwritten(self):
        path = self.path / 'report.json'
        runner.write_report(path, {'original': True})
        with self.assertRaises(runner.BenchmarkError):
            runner.write_report(path, {'original': False})
        self.assertEqual(json.loads(path.read_text()), {'original': True})

    def test_export_is_deterministic_and_excludes_answers(self):
        first, second = self.path / 'one', self.path / 'two'
        self.assertEqual(runner.export_dataset(ROOT, first), {'scenario_groups': 26, 'rows': 78, 'published': False})
        runner.export_dataset(ROOT, second)
        self.assertEqual(runner.dataset_inventory(first), runner.dataset_inventory(second))
        self.assertGreater(len(runner.dataset_inventory(first)), runner.MAX_FILES)
        with self.assertRaises(runner.BenchmarkError):
            runner.inventory(first)
        self.assertFalse(any('references/' in name or 'evaluator/' in name for name in runner.dataset_inventory(first)))
        rows = [json.loads(line) for line in (first / 'tasks.jsonl').read_text().splitlines()]
        self.assertEqual(len({row['scenario_group'] for row in rows}), 26)
        self.assertEqual(len(rows), 78)
        self.assertTrue(all(row['language'] == 'en' and row['benchmark_version'] == '0.4.0' for row in rows))

    def test_release_families_and_calibration_targets(self):
        from collections import Counter
        tasks = runner.list_tasks(ROOT)
        self.assertEqual(sorted(Counter(t['category'] for t in tasks).values()), [4,4,4,4,5,5])
        self.assertEqual(sum(len(t['checks']) for t in tasks), 232)
        self.assertEqual(Counter(t['usage_partition'] for t in tasks), {'development': 6, 'evaluation': 20})
        sources = {s['id'] for s in runner.read_json(ROOT / 'SOURCES.json') if s['status'] == 'retrieved'}
        for task in tasks:
            self.assertEqual(len(task['calibrations']), 3)
            for calibration in task['calibrations']:
                code = (ROOT / 'references' / task['task_id'] / calibration['file']).read_text()
                self.assertEqual(code.count(calibration['find']), 1)
            incident = runner.read_json(ROOT / 'tasks' / task['task_id'] / 'workspace/incident.json')
            self.assertEqual(incident['accepted_change_boundary'], task['editable_files'])
            self.assertTrue(set(task['business_context']['source_refs']) <= sources)
            self.assertIn('OPERATIONS.md', runner.inventory(ROOT / 'tasks' / task['task_id'] / 'workspace'))

    def test_churn_does_not_override_scope_rejection(self):
        submission = self.package(reference=True)
        (submission / 'PROJECT.md').write_text('replacement')
        with mock.patch('subprocess.run') as execute:
            result = runner.evaluate(ROOT, 'invoice_import', submission)
        execute.assert_not_called()
        self.assertFalse(result['accepted'])
        self.assertGreater(result['patch_statistics']['lines_added'], 0)
        self.assertIsNone(result['patch_statistics']['quality_score'])


class RuntimeIntegrationTests(unittest.TestCase):
    def test_actual_container_boundaries(self):
        # A trusted probe runs with the same command and staging as candidates.
        runtime = runner.read_json(ROOT / 'runtime.json')
        with tempfile.TemporaryDirectory(prefix='pmi-probe-') as temp:
            root = Path(temp)
            root.chmod(0o755)
            for name in ['submission', 'evaluator']:
                (root / name).mkdir(mode=0o755)
                (root / name).chmod(0o755)
            probe = root / 'evaluator' / 'worker.py'
            probe.write_text('''import json, os, pathlib, socket
checks = {}
checks['non_root'] = os.getuid() == 65534
checks['no_host_marker'] = 'PMI_BENCH_TEST_SECRET' not in os.environ
checks['no_docker_socket'] = not pathlib.Path('/var/run/docker.sock').exists()
status = pathlib.Path('/proc/self/status').read_text()
checks['no_privileges'] = 'NoNewPrivs:\\t1' in status and 'CapEff:\\t0000000000000000' in status
for directory in ['/submission', '/evaluator', '/etc']:
    try:
        pathlib.Path(directory, 'pmi_probe_write').write_text('x')
        checks[directory + '_readonly'] = False
    except OSError:
        checks[directory + '_readonly'] = True
pathlib.Path('/tmp/writable').write_text('ok')
checks['scratch_writable'] = True
with socket.socket() as sock:
    sock.settimeout(.2)
    checks['no_external_route'] = sock.connect_ex(('1.1.1.1', 443)) != 0
print(json.dumps(checks))
''')
            probe.chmod(0o444)
            name = 'pmi-probe-' + root.name
            command = runner.docker_command(runtime, name, root / 'submission', root / 'evaluator')
            try:
                with mock.patch.dict(os.environ, {'PMI_BENCH_TEST_SECRET': 'synthetic-marker'}):
                    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                checks = json.loads(result.stdout)
                self.assertTrue(checks)
                self.assertTrue(all(checks.values()), checks)
            finally:
                subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=5)
