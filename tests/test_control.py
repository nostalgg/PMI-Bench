import json
import tempfile
import unittest
from pathlib import Path

from pmi_bench import control, runner


class ApprovalControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.binding = {'task':'invoice_import', 'approval_id':'specific-plan-request-workspace'}

    def test_public_plan_hash_does_not_authorize_execution(self):
        (self.directory / 'plan.json').write_text(json.dumps(self.binding))
        with self.assertRaises(runner.BenchmarkError):
            control.consume(self.directory, self.binding)

    def test_operator_record_is_bound_and_one_use(self):
        authority = control.approve(self.directory, self.binding)
        self.assertEqual(authority, 'explicit_operator_command_not_authenticated_identity')
        with self.assertRaises(runner.BenchmarkError):
            control.consume(self.directory, {**self.binding, 'approval_id':'stale'})
        self.assertFalse((self.directory / 'controller/consumed').exists())
        control.consume(self.directory, self.binding)
        with self.assertRaises(runner.BenchmarkError):
            control.consume(self.directory, self.binding)

    def test_modified_or_symlinked_private_record_rejected(self):
        control.approve(self.directory, self.binding)
        private = self.directory / 'controller'
        record = json.loads((private / 'approval.json').read_text())
        record['signature'] = '0' * 64
        (private / 'approval.json').write_text(json.dumps(record))
        with self.assertRaises(runner.BenchmarkError):
            control.consume(self.directory, self.binding)
        (private / 'approval.json').unlink()
        (private / 'approval.json').symlink_to(self.directory / 'plan.json')
        with self.assertRaises(runner.BenchmarkError):
            control.consume(self.directory, self.binding)

    def test_separate_judge_mounts_exclude_oracle_from_candidate(self):
        runtime = runner.read_json(runner.DEFAULT_ROOT / 'runtime.json')
        candidate, judge = runner.isolated_commands(runtime, 'probe', self.directory)
        self.assertFalse(any('dst=/evaluator' in arg or 'dst=/control' in arg for arg in candidate))
        self.assertIn('probe-channel', ' '.join(candidate))
        self.assertIn('--network=none', candidate)
        self.assertIn('--network=container:probe-candidate', judge)
        self.assertIn('type=volume,src=probe-channel,dst=/channel,readonly', judge)
