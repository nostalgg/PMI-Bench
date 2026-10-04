"""Task packaging and Docker evaluation; never imports submission code on the host."""
from __future__ import annotations

import hashlib
import difflib
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


class BenchmarkError(Exception):
    """Configuration or runner failure, not a candidate's incorrect answer."""


DEFAULT_ROOT = Path(__file__).resolve().parents[2] / 'benchmark'
MAX_FILES = 100
MAX_BYTES = 2 * 1024 * 1024
MAX_DATASET_FILES = 2000
MAX_DATASET_BYTES = 64 * 1024 * 1024


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise BenchmarkError(f'Cannot read {path}: {exc}') from exc


def list_tasks(root: Path):
    if not (root / 'tasks').is_dir():
        raise BenchmarkError('Benchmark data not found; use --benchmark-root with the repository benchmark directory')
    tasks = [load_task(root, path.parent.name) for path in sorted((root / 'tasks').glob('*/task.json'))]
    if not tasks or len({task['benchmark_version'] for task in tasks}) != 1:
        raise BenchmarkError('Tasks must form a nonempty, single-version release')
    return tasks


def load_task(root: Path, task_id: str):
    if not task_id or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in task_id):
        raise BenchmarkError('Invalid task identifier')
    task = read_json(root / 'tasks' / task_id / 'task.json')
    if task.get('task_id') != task_id or task.get('schema_version') != 1:
        raise BenchmarkError('Invalid task manifest')
    if set(task.get('prompts', {})) != {'neutral', 'misleading', 'correct'}:
        raise BenchmarkError('Task must define all three request variants')
    checks = task.get('checks', [])
    if not checks or len({c['id'] for c in checks}) != len(checks):
        raise BenchmarkError('Task must declare unique nonempty checks')
    if any(c.get('category') not in {'correctness', 'constraint'} for c in checks):
        raise BenchmarkError('Unknown check category')
    editable = task.get('editable_files', [])
    if not editable or any(Path(p).is_absolute() or '..' in Path(p).parts for p in editable):
        raise BenchmarkError('Invalid editable paths')
    calibration = task.get('calibration', {})
    if (task.get('language') != 'en' or not task.get('benchmark_version')
            or calibration.get('file') not in editable or not calibration.get('find')
            or not isinstance(calibration.get('replace'), str)
            or calibration.get('target_check') not in {check['id'] for check in checks}):
        raise BenchmarkError('Invalid release language or calibration metadata')
    context = task.get('business_context', {})
    if (context.get('realism_level') != 'operational_synthetic'
            or context.get('context_depth') not in {'micro_maintenance', 'operational_workflow', 'integrated_workflow'}
            or not context.get('workflow') or not isinstance(context.get('source_refs'), list)):
        raise BenchmarkError('Missing operational context or provenance')
    if task.get('usage_partition') not in {'development', 'evaluation'}:
        raise BenchmarkError('Missing scenario-group partition')
    calibrations = task.get('calibrations', [calibration])
    if (len(calibrations) != 3 or len({c.get('id') for c in calibrations}) != 3
            or any(c.get('file') not in editable or not c.get('find')
                   or not isinstance(c.get('replace'), str)
                   or c.get('target_check') not in {check['id'] for check in checks}
                   for c in calibrations)):
        raise BenchmarkError('Release requires three distinct targeted regressions per scenario')
    return task


def inventory(directory: Path, *, max_files=MAX_FILES, max_bytes=MAX_BYTES):
    """Reject symlinks, special files and excessive input before staging a submission."""
    if directory.is_symlink() or not directory.is_dir():
        raise BenchmarkError('Submission must be a real directory')
    result = {}
    size = 0
    for parent, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs:
            if (Path(parent) / name).is_symlink():
                raise BenchmarkError('Symlink directories are not supported')
        for name in files:
            path = Path(parent) / name
            if path.is_symlink() or not path.is_file():
                raise BenchmarkError('Symlinks and special files are not supported')
            size += path.stat().st_size
            if size > max_bytes or len(result) >= max_files:
                raise BenchmarkError('Artifact exceeds its file or byte limits')
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def dataset_inventory(directory: Path):
    """Dataset packaging has its own bounds; submission limits stay unchanged."""
    return inventory(directory, max_files=MAX_DATASET_FILES, max_bytes=MAX_DATASET_BYTES)


def digest_map(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def patch_statistics(root, task, submission):
    """Line churn is diagnostic only; it does not score maintainability."""
    changed, added, removed = [], 0, 0
    for name in task['editable_files']:
        original = root / 'tasks' / task['task_id'] / 'workspace' / name
        candidate = submission / name
        if not candidate.is_file():
            continue
        before, after = original.read_bytes(), candidate.read_bytes()
        if before == after:
            continue
        changed.append(name)
        left = before.decode('utf-8', errors='replace').splitlines()
        right = after.decode('utf-8', errors='replace').splitlines()
        for operation, i, j, a, b in difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
            if operation in {'replace', 'delete'}:
                removed += j - i
            if operation in {'replace', 'insert'}:
                added += b - a
    return {'changed_editable_files': changed, 'lines_added': added, 'lines_removed': removed,
            'quality_score': None, 'interpretation': 'Descriptive churn, not a preference for shorter code.'}


def prepare(root: Path, task_id: str, variant: str, destination: Path, reference=False):
    task = load_task(root, task_id)
    if variant not in task['prompts']:
        raise BenchmarkError('Unknown request variant')
    if destination.exists():
        raise BenchmarkError('Destination already exists; refusing to overwrite it')
    source = root / 'tasks' / task_id / 'workspace'
    inventory(source)
    destination.mkdir(parents=True)
    shutil.copytree(source, destination / 'workspace')
    if reference:
        refs = root / 'references' / task_id
        if set(inventory(refs)) != set(task['editable_files']):
            raise BenchmarkError('Reference file set does not match editable paths')
        for name in task['editable_files']:
            shutil.copyfile(refs / name, destination / 'workspace' / name)
    request = {
        'benchmark_version': task['benchmark_version'], 'task_id': task_id, 'variant': variant,
        'request': task['prompts'][variant], 'editable_files': task['editable_files'],
        'approval_protocol': task['approval_protocol'], 'contains_reference': reference,
    }
    (destination / 'request.json').write_text(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
    return request


def scope_changes(root: Path, task, submitted):
    baseline = inventory(root / 'tasks' / task['task_id'] / 'workspace')
    editable = set(task['editable_files'])
    violations = []
    for path in sorted(set(baseline) | set(submitted)):
        if path not in baseline:
            violations.append(f'Unexpected file: {path}')
        elif path not in submitted:
            violations.append(f'Missing file: {path}')
        elif path not in editable and submitted[path] != baseline[path]:
            violations.append(f'Protected file changed: {path}')
    return violations


def docker_command(runtime, name, submission, evaluator):
    return [
        'docker', 'run', '--rm', '--pull=never', '--name', name,
        '--network=none', '--read-only', '--user', '65534:65534',
        '--cap-drop=ALL', '--security-opt=no-new-privileges',
        '--pids-limit', str(runtime['pids_limit']), '--memory', runtime['memory'],
        '--memory-swap', runtime['memory'], '--cpus', runtime['cpus'],
        '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,size=67108864,mode=1777',
        '--mount', f'type=bind,src={submission},dst=/submission,readonly',
        '--mount', f'type=bind,src={evaluator},dst=/evaluator,readonly',
        '--workdir', '/tmp', '--env', 'PYTHONDONTWRITEBYTECODE=1',
        runtime['image'], 'python', '-I', '-B', '/evaluator/worker.py',
    ]


def stage_readonly(source: Path, destination: Path):
    shutil.copytree(source, destination)
    for parent, dirs, files in os.walk(destination):
        Path(parent).chmod(0o755)
        for file in files:
            (Path(parent) / file).chmod(0o444)


def validate_payload(task, payload, exit_code):
    expected = {c['id']: c['category'] for c in task['checks']}
    checks = payload.get('checks', [])
    actual = {c.get('id'): c.get('category') for c in checks}
    if (payload.get('task_id') != task['task_id'] or actual != expected
            or len(checks) != len(expected) or payload.get('tests_run') != len(expected)):
        raise BenchmarkError('Evaluator did not execute the exact declared check set')
    if any(c.get('status') not in {'pass', 'fail', 'error', 'skip'} for c in checks):
        raise BenchmarkError('Invalid evaluator check status')
    passed = all(c['status'] == 'pass' for c in checks)
    if exit_code != (0 if passed else 1):
        raise BenchmarkError('Evaluator exit status contradicts its results')
    return checks


def evaluate(root: Path, task_id: str, submission: Path, variant='neutral'):
    task = load_task(root, task_id)
    if variant not in task['prompts']:
        raise BenchmarkError('Unknown request variant')
    runtime = read_json(root / 'runtime.json')
    if '@sha256:' not in runtime['image']:
        raise BenchmarkError('Evaluation image must be pinned by digest')
    files = inventory(submission)
    violations = scope_changes(root, task, files)
    report = {
        'schema_version': 1, 'benchmark_version': task['benchmark_version'],
        'run_id': uuid.uuid4().hex, 'created_at': datetime.now(timezone.utc).isoformat(),
        'task_id': task_id, 'variant': variant, 'image': runtime['image'],
        'submission_sha256': digest_map(files), 'submission_files': files,
        'task_sha256': hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest(),
        'evaluator_sha256': digest_map(inventory(root / 'evaluator')),
        'scope_violations': violations, 'checks': [], 'accepted': False,
        'patch_statistics': patch_statistics(root, task, submission),
        'agent_behavior': {'plan_approval': 'not_measured', 'sycophancy': 'not_measured',
                           'maintainability': 'requires_human_review', 'model_cost': None},
    }
    if violations:
        report['status'] = 'scope_violation'
        return report
    if not shutil.which('docker'):
        raise BenchmarkError('Docker is required; host execution is intentionally unsupported')
    start = time.monotonic()
    name = 'pmi-bench-' + report['run_id']
    with tempfile.TemporaryDirectory(prefix='pmi-bench-') as temp:
        stage = Path(temp)
        stage.chmod(0o755)
        stage_readonly(submission, stage / 'submission')
        stage_readonly(root / 'evaluator', stage / 'evaluator')
        # Recheck the staged snapshot rather than racing evaluation against live edits.
        if inventory(stage / 'submission') != files:
            raise BenchmarkError('Submission changed while it was being staged')
        command = docker_command(runtime, name, stage / 'submission', stage / 'evaluator') + [task_id]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=runtime['timeout_seconds'], check=False)
        except subprocess.TimeoutExpired:
            report.update(status='timeout', error='Container exceeded the wall-clock limit')
        else:
            report['container_exit_code'] = process.returncode
            if process.returncode in {125, 126, 127}:
                report.update(status='infrastructure_error', error=process.stderr[-2000:])
            elif process.returncode not in {0, 1}:
                report.update(status='execution_error', error=process.stderr[-2000:])
            else:
                try:
                    checks = validate_payload(task, json.loads(process.stdout), process.returncode)
                    report['checks'] = checks
                    report['accepted'] = all(c['status'] == 'pass' for c in checks)
                    report['status'] = 'passed' if report['accepted'] else 'failed'
                except (BenchmarkError, ValueError, TypeError, AttributeError) as exc:
                    report.update(status='evaluation_error', error=str(exc))
        finally:
            # Clean up only the container named for this run, including on timeout.
            try:
                subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=10, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
    report['wall_seconds'] = round(time.monotonic() - start, 3)
    report['counts'] = {status: sum(c['status'] == status for c in report['checks'])
                        for status in ['pass', 'fail', 'error', 'skip']}
    report['scores'] = {
        category: {
            'passed': sum(c['category'] == category and c['status'] == 'pass' for c in report['checks']),
            'total': sum(c['category'] == category for c in task['checks']),
        }
        for category in ['correctness', 'constraint']
    }
    return report


def write_report(path: Path, report):
    if path.exists():
        raise BenchmarkError('Report already exists; use a new output path')
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects against a race between the check and write.
    with path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def self_test(root: Path, task_ids=None, jobs=1):
    """Evaluate originals, references and every declared targeted regression."""
    runs = []
    tasks = list_tasks(root)
    if task_ids is not None:
        if not task_ids or not set(task_ids) <= {t['task_id'] for t in tasks}:
            raise BenchmarkError('Unknown or empty calibration task selection')
        tasks = [t for t in tasks if t['task_id'] in task_ids]
    if not isinstance(jobs, int) or isinstance(jobs, bool) or not 1 <= jobs <= 4:
        raise BenchmarkError('Calibration jobs must be between one and four')
    with tempfile.TemporaryDirectory(prefix='pmi-self-test-') as temp:
        def run_task(task):
            task_runs = []
            task_id = task['task_id']
            candidates = [('baseline', None), ('reference', None)]
            candidates += [('mutation', c) for c in task['calibrations']]
            for kind, calibration in candidates:
                mutation_id = calibration['id'] if calibration else None
                destination = Path(temp) / task_id / (mutation_id or kind)
                prepare(root, task_id, 'neutral', destination, reference=kind != 'baseline')
                if kind == 'mutation':
                    filename = calibration['file']
                    before, after = calibration['find'], calibration['replace']
                    path = destination / 'workspace' / filename
                    code = path.read_text()
                    if code.count(before) != 1:
                        raise BenchmarkError('Mutation no longer matches its reference')
                    path.write_text(code.replace(before, after))
                result = evaluate(root, task_id, destination / 'workspace')
                result['candidate_kind'] = kind
                result['mutation_id'] = mutation_id
                result['expected_outcome_observed'] = (
                    result['status'] == ('passed' if kind == 'reference' else 'failed')
                    and (kind == 'reference' or any(c['status'] in {'fail', 'error'} for c in result['checks']))
                    and (kind != 'mutation' or any(
                        c['id'] == calibration['target_check'] and c['status'] in {'fail', 'error'}
                        for c in result['checks']))
                )
                task_runs.append(result)
            return task_runs
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            for task_runs in executor.map(run_task, tasks):
                runs.extend(task_runs)
    return {'benchmark_version': tasks[0]['benchmark_version'], 'runs': runs,
            'self_test_passed': bool(runs) and all(r['expected_outcome_observed'] for r in runs)}


def export_dataset(root: Path, destination: Path):
    """Write a publication draft without solutions/evaluator or any network operation."""
    if destination.exists():
        raise BenchmarkError('Export destination already exists')
    tasks = list_tasks(root)
    destination.mkdir(parents=True)
    with (destination / 'tasks.jsonl').open('w', encoding='utf-8') as stream:
        for task in tasks:
            for variant, prompt in task['prompts'].items():
                row = {key: task[key] for key in ['task_id', 'title', 'category', 'benchmark_version', 'language',
                                                 'editable_files', 'provenance', 'checks', 'approval_protocol',
                                                 'business_context', 'evaluation_dimensions']}
                row['usage_partition'] = task['usage_partition']
                row['workflow_contract'] = task['workflow_contract']
                row.update(variant=variant, request=prompt, scenario_group=task['task_id'])
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            source = root / 'tasks' / task['task_id'] / 'workspace'
            inventory(source)
            shutil.copytree(source, destination / 'workspaces' / task['task_id'])
    shutil.copyfile(root / 'DATASET_CARD.md', destination / 'DATASET_CARD.md')
    shutil.copyfile(root / 'SOURCES.json', destination / 'SOURCES.json')
    for document in ['SCENARIOS.csv', 'PROTOCOL.md', 'REVIEW_RUBRIC.md']:
        shutil.copyfile(root / document, destination / document)
    for document in ['LICENSE', 'LICENSE-DATA', 'LICENSING.md']:
        shutil.copyfile(root.parent / document, destination / document)
    shutil.copytree(root / 'dialogue', destination / 'dialogue')
    (destination / 'PUBLICATION_PENDING.txt').write_text(
        'Kaggle upload pending: provide your actual Kaggle owner/slug and authenticated upload.\n'
        'Code: Apache 2.0. Data/documentation: CC BY 4.0. See LICENSING.md.\n'
        'No Kaggle upload or competition has been created. Evaluator and references are in the GitHub source.\n'
    )
    (destination / 'export-manifest.json').write_text(json.dumps({
        'benchmark_version': tasks[0]['benchmark_version'], 'schema_version': 1,
        'files': dataset_inventory(destination),
    }, sort_keys=True, indent=2) + '\n')
    return {'scenario_groups': len(tasks), 'rows': sum(len(t['prompts']) for t in tasks),
            'published': False}
