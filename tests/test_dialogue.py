import copy
import unittest
from pathlib import Path

from pmi_bench.dialogue import audit_dialogue
from pmi_bench.runner import BenchmarkError, DEFAULT_ROOT, read_json


class DialogueTests(unittest.TestCase):
    def setUp(self):
        self.log = read_json(DEFAULT_ROOT/'dialogue/example-transcript.json')

    def test_complete_explicit_protocol(self):
        report = audit_dialogue(DEFAULT_ROOT, 'invoice_import', self.log)
        self.assertTrue(report['structural_conformance'])
        self.assertEqual(report['semantic_quality'], 'requires_human_review')

    def rejected(self, log):
        with self.assertRaises(BenchmarkError):
            audit_dialogue(DEFAULT_ROOT, 'invoice_import', log)

    def test_edit_without_approval(self):
        del self.log['events'][3]
        self.rejected(self.log)

    def test_revised_plan_invalidates_approval(self):
        plan = copy.deepcopy(self.log['events'][2]); plan['plan']['version'] = 2
        self.log['events'].insert(4, plan)
        self.rejected(self.log)

    def test_request_or_workspace_changed(self):
        self.log['binding']['request_sha256'] = '0'*64
        self.rejected(self.log)
        self.setUp()
        self.log['events'][4]['before_sha256'] = '0'*64
        self.rejected(self.log)

    def test_no_plan_before_clarification(self):
        del self.log['events'][:2]
        self.rejected(self.log)

    def test_unapproved_or_wrong_role(self):
        self.log['events'][3]['role'] = 'assistant'
        self.rejected(self.log)

    def test_protected_file_not_allowed_in_plan(self):
        self.log['events'][2]['plan']['editable_files'].append('consumer.py')
        self.rejected(self.log)

    def test_plan_revision_budget(self):
        for version in [2,3,4]:
            plan = copy.deepcopy(self.log['events'][2]); plan['plan']['version'] = version
            self.log['events'].insert(version + 1, plan)
        self.rejected(self.log)

    def test_incomplete_and_post_final_events(self):
        missing = copy.deepcopy(self.log); missing['events'].pop()
        self.rejected(missing)
        self.log['events'].append(self.log['events'][-1])
        self.rejected(self.log)
