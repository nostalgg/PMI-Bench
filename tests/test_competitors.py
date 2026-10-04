import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('competitor_runner', ROOT / 'competitors/run.py')
competitors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(competitors)


class CompetitorTests(unittest.TestCase):
    def test_prompt_or_empty_response_is_not_a_plan(self):
        prompt_only = 'TO LLM 2026-10-04\nUSER propose a plan\nLLM RESPONSE 2026-10-04\n'
        self.assertEqual(competitors.aider_responses(prompt_only), '')
        reply = prompt_only + 'ASSISTANT Validate the input first.\nASSISTANT Use a transaction.\n'
        self.assertEqual(competitors.aider_responses(reply), 'Validate the input first.\nUse a transaction.')

    def test_missing_key_never_invokes_agent(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / 'untouched'
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch('subprocess.run') as execute:
                result = competitors.main(['--agent', 'aider', '--python', '/bin/python',
                    '--model', 'openrouter/explicit-model', '--mode', 'plan', '--task', 'invoice_import',
                    '--run-dir', str(directory)])
            self.assertEqual(result, 2)
            self.assertFalse(directory.exists())
            execute.assert_not_called()

    def test_approval_bound_to_plan_request_and_workspace(self):
        original = competitors.approval_id('plan', {'request': 'x'}, {'file': 'hash'})
        for args in [('changed', {'request': 'x'}, {'file': 'hash'}),
                     ('plan', {'request': 'changed'}, {'file': 'hash'}),
                     ('plan', {'request': 'x'}, {'file': 'changed'})]:
            self.assertNotEqual(original, competitors.approval_id(*args))

    def test_execution_without_approval_never_invokes_agent(self):
        from pmi_bench import runner
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / 'run'
            request = runner.prepare(runner.DEFAULT_ROOT, 'invoice_import', 'neutral', directory)
            plan = {'agent': 'aider', 'model': 'openrouter/explicit-model', 'task': 'invoice_import',
                    'variant': 'neutral', 'text': 'Use a transaction.'}
            plan['approval_id'] = competitors.approval_id(plan['text'], request, runner.inventory(directory / 'workspace'))
            (directory / 'plan.json').write_text(json.dumps(plan))
            with mock.patch.dict(os.environ, {'OPENROUTER_API_KEY': 'synthetic-presence-only'}), mock.patch('subprocess.run') as execute:
                result = competitors.main(['--agent', 'aider', '--python', str(Path(os.sys.executable)),
                    '--model', plan['model'], '--mode', 'execute', '--task', plan['task'], '--run-dir', str(directory)])
            self.assertEqual(result, 2)
            self.assertFalse((directory / 'execute').exists())
            execute.assert_not_called()
