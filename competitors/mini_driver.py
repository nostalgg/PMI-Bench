"""Pinned mini-SWE-agent adapter; inference runs on host, actions inside Docker."""
import argparse
import json
import subprocess
from pathlib import Path

from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.docker import DockerEnvironment
from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel


def run(settings, scripted=None):
    workspace = Path(settings['workspace']).resolve()
    for path in [workspace, *workspace.rglob('*')]:
        path.chmod(0o777 if path.is_dir() else 0o666)
    readonly = ',readonly' if settings['mode'] == 'plan' else ''
    env = DockerEnvironment(image=settings['image'], cwd='/workspace', timeout=30,
        interpreter=['bash', '-c'], container_timeout='1000s', run_args=[
            '--rm', '--pull=never', '--network=none', '--read-only', '--user=65534:65534',
            '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64',
            '--memory=256m', '--cpus=1', '--tmpfs=/tmp:rw,nosuid,nodev,size=67108864,mode=1777',
            '--env=PYTHONDONTWRITEBYTECODE=1',
            '--mount', f'type=bind,src={workspace},dst=/workspace{readonly}'])
    if settings.get('container_id_file'):
        Path(settings['container_id_file']).write_text(env.container_id)
    model = scripted or LitellmTextbasedModel(model_name=settings['model'],
        model_kwargs={'temperature': 0, 'max_tokens': 2048, 'timeout': 60}, cost_tracking='default')
    system = ('You maintain a small Python/SQL business project. Follow PROJECT.md and the request. '
              'Every response must contain exactly one bash action in a fenced block tagged '
              'mswea_bash_command. Work only in /workspace. Do not create extra files. '
              'Finish with an action that prints COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT on its '
              'first line, followed by your final explanation or plan. ')
    system += ('Read files and present a specific plan. Do not edit any file; approval is pending.'
               if settings['mode'] == 'plan' else
               'The attached versioned plan has been explicitly approved. Implement only that plan.')
    agent = DefaultAgent(model, env, system_template=system, instance_template='{{task}}',
                         step_limit=20, cost_limit=settings['soft_budget_usd'],
                         wall_time_limit_seconds=900)
    try:
        agent.run(settings['prompt'])
        result = agent.save(Path(settings['trajectory']))
        return {'exit_status': result['info']['exit_status'],
                'text': result['info']['submission'], 'stats': result['info']['model_stats']}
    finally:
        # Deterministic cleanup instead of the framework's asynchronous destructor.
        if env.container_id:
            subprocess.run(['docker', 'rm', '-f', env.container_id], capture_output=True, timeout=10)
            env.container_id = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('settings', type=Path)
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text())
    result = run(settings)
    Path(settings['response']).write_text(json.dumps(result, indent=2) + '\n')
