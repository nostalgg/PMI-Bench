"""Real agent loop + real Docker, scripted model. NOT a model-performance run."""
import json
import tempfile
from pathlib import Path

from mini_driver import run


class ScriptedModel:
    def __init__(self, commands):
        self.commands = iter(commands)

    def query(self, messages):
        return {'role': 'assistant', 'content': 'Scripted adapter check',
                'extra': {'actions': [{'command': next(self.commands)}], 'cost': 0.0}}

    def format_message(self, **kwargs):
        return kwargs

    def format_observation_messages(self, message, outputs, template_vars=None):
        return [{'role': 'user', 'content': json.dumps(outputs)}]

    def get_template_vars(self):
        return {}

    def serialize(self):
        return {'scripted_model': True}


def main():
    root = Path(__file__).resolve().parents[1]
    image = json.loads((root / 'benchmark/runtime.json').read_text())['image']
    with tempfile.TemporaryDirectory(prefix='pmi-mini-smoke-') as temporary:
        directory = Path(temporary)
        directory.chmod(0o755)
        workspace = directory / 'workspace'
        workspace.mkdir()
        (workspace / 'probe.py').write_text('original\n')
        settings = {'workspace': str(workspace), 'mode': 'plan', 'model': 'scripted-no-inference',
                    'image': image, 'soft_budget_usd': 1, 'prompt': 'Adapter smoke test only.',
                    'trajectory': str(directory / 'trajectory.json')}
        result = run(settings, ScriptedModel([
            'printf changed > probe.py',
            'printf "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\\nA specific test plan\\n"']))
        assert result['exit_status'] == 'Submitted'
        assert (workspace / 'probe.py').read_text() == 'original\n'
        settings['mode'] = 'execute'
        result = run(settings, ScriptedModel([
            'printf changed > probe.py',
            'printf "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\\nDone\\n"']))
        assert result['exit_status'] == 'Submitted'
        assert (workspace / 'probe.py').read_text() == 'changed'
        assert result['stats']['api_calls'] == 2
        assert result['stats']['instance_cost'] == 0
    print('mini-SWE-agent integration passed: planning read-only; execution changes copied workspace; no inference.')


if __name__ == '__main__':
    main()
