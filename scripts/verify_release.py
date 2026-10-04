"""Verify frozen source hashes and checked-in calibration, without executing candidates."""
import hashlib
import json
from pathlib import Path

from pmi_bench import runner

ROOT = Path(__file__).resolve().parents[1]


def verify():
    release=runner.read_json(ROOT/'benchmark/RELEASE.json')
    for name,expected in release['files'].items():
        path=ROOT/name
        if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise runner.BenchmarkError('Frozen release differs: '+name)
    report=runner.read_json(ROOT/'docs/validation/calibration-05.json')
    if not report['self_test_passed'] or len(report['runs'])!=130:
        raise runner.BenchmarkError('Incomplete core evidence')
    evaluator_hash=runner.digest_map(runner.inventory(ROOT/'benchmark/evaluator'))
    bridge_hash=runner.digest_map(runner.inventory(ROOT/'benchmark/bridge'))
    references=negative=checks=0
    for run in report['runs']:
        task=runner.load_task(ROOT/'benchmark',run['task_id'])
        task_hash=hashlib.sha256(json.dumps(task,sort_keys=True).encode()).hexdigest()
        if (run['task_sha256']!=task_hash or run['evaluator_sha256']!=evaluator_hash
                or run['bridge_sha256']!=bridge_hash or not run['expected_outcome_observed']):
            raise runner.BenchmarkError('Stale or unsuccessful calibration evidence')
        files=runner.inventory(ROOT/'benchmark/tasks'/task['task_id']/'workspace')
        if run['candidate_kind']!='baseline':
            files.update(runner.inventory(ROOT/'benchmark/references'/task['task_id']))
        if run['candidate_kind']=='mutation':
            calibration=next(c for c in task['calibrations'] if c['id']==run['mutation_id'])
            code=(ROOT/'benchmark/references'/task['task_id']/calibration['file']).read_text()
            files[calibration['file']]=hashlib.sha256(code.replace(calibration['find'],calibration['replace']).encode()).hexdigest()
        if run['submission_files']!=files or run['submission_sha256']!=runner.digest_map(files):
            raise runner.BenchmarkError('Submission evidence differs from frozen inputs')
        if run['candidate_kind']=='reference':
            references+=1;checks+=len(run['checks'])
            if not run['accepted']: raise runner.BenchmarkError('Reference rejected')
        else:
            negative+=1
            if run['accepted']: raise runner.BenchmarkError('Regression accepted')
    if (references,negative,checks)!=(26,104,258): raise runner.BenchmarkError('Unexpected release counts')
    profile=runner.read_json(ROOT/'docs/validation/profiles-05.json')
    if not profile['self_test_passed'] or len(profile['runs'])!=18:
        raise runner.BenchmarkError('Incomplete profile evidence')
    for name,expected in [('profiles/worker.py',profile['worker_sha256']),('profiles/requirements.lock',profile['requirements_sha256'])]:
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise runner.BenchmarkError('Stale profile source/dependencies')
    judge_files=runner.inventory(ROOT/'benchmark/evaluator')
    judge_files['worker.py']=profile['worker_sha256']
    if (profile['bridge_sha256']!=bridge_hash or profile['judge_evaluator_sha256']!=runner.digest_map(judge_files)
            or profile['reference_checks']!=24):
        raise runner.BenchmarkError('Stale profile judge evidence')
    for run in profile['runs']:
        task=runner.load_task(ROOT/'benchmark',run['task_id'])
        task_hash=hashlib.sha256(json.dumps(task,sort_keys=True).encode()).hexdigest()
        files=runner.inventory(ROOT/'benchmark/tasks'/task['task_id']/'workspace')
        if run['candidate_kind']!='baseline':
            files.update(runner.inventory(ROOT/'benchmark/references'/task['task_id']))
        if run['candidate_kind']=='mutation':
            calibration=task['calibrations'][1 if task['task_id']=='incremental_sync' else 0]
            code=(ROOT/'benchmark/references'/task['task_id']/calibration['file']).read_text()
            files[calibration['file']]=hashlib.sha256(code.replace(calibration['find'],calibration['replace']).encode()).hexdigest()
        if (run['task_sha256']!=task_hash or run['submission_sha256']!=runner.digest_map(files)
                or not run['expected_outcome_observed']):
            raise runner.BenchmarkError('Stale or unsuccessful profile submission evidence')
    probe=profile['capability_probe']
    if not probe['expected_outcome_observed'] or probe['accepted']:
        raise runner.BenchmarkError('PostgreSQL capability attack was not rejected')
    attack=runner.read_json(ROOT/'docs/validation/adversarial-05.json')
    if not attack['self_test_passed'] or len(attack['runs'])!=5:
        raise runner.BenchmarkError('Incomplete adversarial evidence')
    if hashlib.sha256((ROOT/'scripts/validate_adversarial.py').read_bytes()).hexdigest()!=attack['script_sha256']:
        raise runner.BenchmarkError('Stale adversarial fixture evidence')
    for run in attack['runs']:
        if (run['bridge_sha256']!=bridge_hash or run['evaluator_sha256']!=evaluator_hash
                or not run['expected_outcome_observed'] or run['accepted']):
            raise runner.BenchmarkError('Stale or unsuccessful adversarial evidence')
    dialogue=runner.read_json(ROOT/'docs/validation/dialogue-05.json')
    if (dialogue['valid_logs'],dialogue['invalid_logs_rejected'],dialogue['agent_runs'])!=(26,130,0):
        raise runner.BenchmarkError('Unexpected dialogue evidence')
    source_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/pmi_bench').glob('*.py')}
    if dialogue['auditor_sha256']!=runner.digest_map(source_files):
        raise runner.BenchmarkError('Stale dialogue auditor evidence')
    for record, field in [('unit-tests-05.json','test_sources'),('adapter-smokes-05.json','sources')]:
        evidence=runner.read_json(ROOT/'docs/validation'/record)
        for name,expected in evidence[field].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
                raise runner.BenchmarkError('Stale test/adapter evidence: '+name)
    return {'version':release['benchmark_version'],'frozen_files_verified':len(release['files']),
            'core_references':references,'core_negative_candidates':negative,'core_reference_checks':checks,
            'dependency_runs':18,'scripted_attacks_rejected':5,'real_model_runs':0}


if __name__=='__main__': print(json.dumps(verify()))
