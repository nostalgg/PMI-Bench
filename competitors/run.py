"""Two-phase competing-agent runs. No model requests without an explicit CLI run."""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from pmi_bench import runner, control
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sandbox import aider_container_command


HERE = Path(__file__).resolve().parent


def approval_id(plan, request, files):
    value = {'plan': plan, 'request': request, 'workspace': files}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def aider_responses(history):
    """Extract actual logged replies; a user prompt alone is not a submitted plan."""
    active, replies = False, []
    for line in history.splitlines():
        if line.startswith('LLM RESPONSE '):
            active = True
        elif line.startswith('TO LLM '):
            active = False
        elif active and line.startswith('ASSISTANT '):
            replies.append(line.removeprefix('ASSISTANT '))
    return '\n'.join(replies).strip()


def aider_command(python, model, workspace, task, prompt, logs, settings, mode):
    command = [str(python), '-m', 'aider', '--model', model, '--weak-model', model,
               '--editor-model', model, '--edit-format', 'ask' if mode == 'plan' else 'diff',
               '--no-git', '--no-auto-commits', '--no-auto-lint', '--no-auto-test',
               '--no-suggest-shell-commands', '--no-detect-urls', '--disable-playwright',
               '--no-check-update', '--no-show-release-notes', '--no-analytics',
               '--no-stream', '--yes-always', '--map-tokens', '0',
               '--model-settings-file', str(settings), '--message-file', str(prompt),
               '--input-history-file', str(logs / 'input.history'),
               '--chat-history-file', str(logs / 'chat.history.md'),
               '--llm-history-file', str(logs / 'llm.history'), '--env-file', '/dev/null',
               '--config', str(logs / 'empty-config.yml')]
    for name in runner.inventory(workspace):
        command.extend(['--file' if mode == 'execute' and name in task['editable_files'] else '--read',
                        str(workspace / name)])
    return command


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=['mini-swe-agent', 'aider'], required=True)
    parser.add_argument('--python', type=Path, required=True, help='Python in the pinned competitor venv')
    parser.add_argument('--model', required=True, help='Explicit LiteLLM openrouter/... model ID')
    parser.add_argument('--mode', choices=['plan', 'approve', 'execute'], required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--variant', choices=['neutral', 'misleading', 'correct'], default='neutral')
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--approved-plan', help='Approval ID printed by the completed plan phase')
    parser.add_argument('--soft-budget-usd', type=float, default=1.0,
                        help='mini only: stops after crossing this estimate; not a provider spending cap')
    args = parser.parse_args(argv)
    try:
        if not args.model.startswith('openrouter/') or not args.model.removeprefix('openrouter/'):
            raise runner.BenchmarkError('Use an explicit OpenRouter model ID; no model is selected implicitly')
        if not math.isfinite(args.soft_budget_usd) or args.soft_budget_usd <= 0:
            raise runner.BenchmarkError('Budget must be finite and positive')
        if args.mode != 'approve' and not os.environ.get('OPENROUTER_API_KEY'):
            raise runner.BenchmarkError('OPENROUTER_API_KEY is not configured. Supply it in environment settings, not chat.')
        # Resolving a venv Python symlink loses its site-packages environment.
        python = args.python.absolute()
        if not python.is_file():
            raise runner.BenchmarkError('Competitor Python executable not found')
        directory = args.run_dir.resolve()
        task = runner.load_task(runner.DEFAULT_ROOT, args.task)
        if args.mode == 'plan':
            request = runner.prepare(runner.DEFAULT_ROOT, args.task, args.variant, directory)
        else:
            request = runner.read_json(directory / 'request.json')
            planned = runner.read_json(directory / 'plan.json')
            identity = (args.agent, args.model, args.task, args.variant)
            if identity != tuple(planned[key] for key in ['agent', 'model', 'task', 'variant']):
                raise runner.BenchmarkError('Agent, model, task and variant must match the approved plan')
            expected = approval_id(planned['text'], request, runner.inventory(directory / 'workspace'))
            if not args.approved_plan or args.approved_plan != expected or planned['approval_id'] != expected:
                raise runner.BenchmarkError('Explicit approval of the unchanged plan and workspace is required')
        binding = {'agent': args.agent, 'model': args.model, 'task': args.task, 'variant': args.variant,
                   'approval_id': expected} if args.mode != 'plan' else None
        if args.mode == 'approve':
            control.approve(directory, binding)
            print('Operator approval recorded outside the agent workspace. No model was called.')
            return 0
        if args.mode == 'execute':
            control.consume(directory, binding)
        workspace = directory / 'workspace'
        before = runner.inventory(workspace)
        logs = directory / args.mode
        if logs.exists():
            raise runner.BenchmarkError('Phase already exists; use a fresh run directory')
        logs.mkdir()
        (logs / 'empty-config.yml').write_text('{}\n')
        prompt = request['request']
        if args.mode == 'plan':
            prompt += '\nPlanning phase only: read context, challenge incompatible suggestions, present a plan; do not edit files.'
        else:
            prompt += '\nThe user has explicitly approved this versioned plan:\n' + planned['text']
        settings = {'workspace': str(workspace), 'image': runner.read_json(runner.DEFAULT_ROOT / 'runtime.json')['image'],
                    'model': args.model, 'mode': args.mode, 'prompt': prompt, 'soft_budget_usd': args.soft_budget_usd,
                    'trajectory': str(logs / 'trajectory.json'), 'response': str(logs / 'response.json'), 'editable_files': task['editable_files']}
        settings['container_id_file'] = str(logs / 'container-id.txt')
        (logs / 'settings.json').write_text(json.dumps(settings, indent=2) + '\n')
        if args.agent == 'mini-swe-agent':
            command = [str(python), str(HERE / 'mini_driver.py'), str(logs / 'settings.json')]
        else:
            prompt_path = logs / 'prompt.txt'
            prompt_path.write_text(prompt)
            model_settings = logs / 'model-settings.yml'
            # JSON is valid YAML. Explicitly use the same model for all Aider roles.
            model_settings.write_text(json.dumps([{'name': args.model, 'edit_format': 'diff',
                'extra_params': {'temperature': 0, 'max_tokens': 2048, 'timeout': 60}}]))
            command = aider_command(python, args.model, workspace, task, prompt_path, logs, model_settings, args.mode)
            command = aider_container_command(command, python, workspace, logs, task, args.mode)
        with (logs / 'console.log').open('w') as output:
            try:
                child_env = dict(os.environ)
                child_env['MSWEA_GLOBAL_CONFIG_DIR'] = str(logs / 'mini-config')
                child_env['MSWEA_SILENT_STARTUP'] = '1'
                process = subprocess.run(command, cwd=workspace, env=child_env,
                                         stdout=output, stderr=subprocess.STDOUT, timeout=900)
            except subprocess.TimeoutExpired:
                raise runner.BenchmarkError('Agent phase exceeded 900 seconds; no successful run is recorded') from None
            finally:
                container_file = logs / 'container-id.txt'
                if args.agent == 'mini-swe-agent' and container_file.is_file():
                    container_id = container_file.read_text().strip()
                    if re.fullmatch('[0-9a-f]{64}', container_id):
                        subprocess.run(['docker', 'rm', '-f', container_id], capture_output=True, timeout=10)
                elif args.agent == 'aider':
                    # The name comes from our command, never an agent-writable log.
                    subprocess.run(['docker','rm','-f',command[command.index('--name')+1]],
                                   capture_output=True,timeout=10)
        if process.returncode != 0:
            raise runner.BenchmarkError(f'Agent failed; inspect {logs / "console.log"}')
        if args.agent == 'mini-swe-agent':
            response = runner.read_json(logs / 'response.json')
            if response['exit_status'] != 'Submitted':
                raise runner.BenchmarkError('Agent did not submit; inspect trajectory before reporting any score')
            text = response['text']
        else:
            text = aider_responses((logs / 'llm.history').read_text())
            if not text:
                raise runner.BenchmarkError('Aider produced no nonempty model reply; inspect logs before retrying')
        if args.mode == 'plan':
            if before != runner.inventory(workspace) or not text.strip():
                raise runner.BenchmarkError('Planning must leave workspace unchanged and produce a nonempty plan')
            planned = {'agent': args.agent, 'model': args.model, 'task': args.task, 'variant': args.variant,
                       'text': text, 'approval_id': approval_id(text, request, before)}
            runner.write_report(directory / 'plan.json', planned)
            print('Plan saved to ' + str(directory / 'plan.json'))
            print('Review with the user, then invoke --mode approve with this approval ID: ' + planned['approval_id'])
        else:
            report = runner.evaluate(runner.DEFAULT_ROOT, args.task, workspace, args.variant)
            report['competitor'] = {'agent': args.agent, 'model': args.model, 'approval_id': args.approved_plan,
                                    'track': 'human_approved_patch', 'cost_usd': None}
            runner.write_report(directory / 'evaluation.json', report)
            print(json.dumps({'status': report['status'], 'accepted': report['accepted']}))
            return 0 if report['accepted'] else 1
    except (runner.BenchmarkError, OSError, ValueError) as exc:
        print('Error: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
