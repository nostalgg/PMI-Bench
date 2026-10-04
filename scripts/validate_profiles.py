"""Supplementary candidate calibration: real PostgreSQL and scientific libraries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from pmi_bench import runner

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {'inventory_ledger':'test_conflict','incremental_sync':'test_order_and_delete','scd_history':'test_close_absent','document_cache':'test_alignment','supplier_catalog':'test_dataframe_producer','temporal_features':'test_training_imputer_agreement'}
POSTGRES = set(TARGETS)-{'supplier_catalog','temporal_features'}


def checked(command, **kwargs):
    return subprocess.run(command,check=True,capture_output=True,text=True,timeout=60,**kwargs)


def calibrate():
    config = runner.read_json(ROOT/'profiles/runtime.json')
    image = json.loads(checked(['docker','image','inspect',config['profile_image']]).stdout)[0]
    if image['Config'].get('Labels',{}).get('org.pmi-bench.requirements-sha256') != config['requirements_sha256']:
        raise runner.BenchmarkError('Rebuild profiles with the committed dependency lock')
    worker_hash = hashlib.sha256((ROOT/'profiles/worker.py').read_bytes()).hexdigest()
    label = 'pmi-profiles-'+uuid.uuid4().hex
    database = label+'-database'
    created_network = created_database = False
    runs = []
    try:
        checked(['docker','network','create','--internal',label]); created_network = True
        checked(['docker','run','-d','--pull=never','--name',database,'--network',label,'--network-alias','pmi-database','--read-only','--user','70:70','--cap-drop=ALL','--security-opt=no-new-privileges','--memory','256m','--memory-swap','256m','--cpus','1','--pids-limit','64','--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=134217728,uid=70,gid=70,mode=0700','--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=1048576,uid=70,gid=70','--env','POSTGRES_USER=benchmark','--env','POSTGRES_DB=benchmark','--env','POSTGRES_PASSWORD=synthetic-fixture-only',config['postgres_image']]); created_database=True
        deadline = time.monotonic()+30
        while time.monotonic()<deadline:
            status=subprocess.run(['docker','exec',database,'pg_isready','-U','benchmark','-d','benchmark'],capture_output=True,timeout=5)
            if status.returncode==0: break
            time.sleep(.25)
        else: raise runner.BenchmarkError('PostgreSQL readiness failed')
        with tempfile.TemporaryDirectory(prefix='pmi-profile-eval-') as temporary:
            folder = Path(temporary); folder.chmod(0o755)
            runner.stage_readonly(ROOT/'profiles',folder/'evaluator')
            for task_id, target in TARGETS.items():
                task=runner.load_task(runner.DEFAULT_ROOT,task_id)
                for kind in ['baseline','reference','mutation']:
                    prepared=folder/task_id/kind
                    runner.prepare(runner.DEFAULT_ROOT,task_id,'neutral',prepared,reference=kind!='baseline')
                    if kind=='mutation':
                        calibration=task['calibrations'][1 if task_id=='incremental_sync' else 0]
                        path=prepared/'workspace'/calibration['file'];code=path.read_text()
                        if code.count(calibration['find'])!=1: raise runner.BenchmarkError('Profile mutation no longer matches')
                        path.write_text(code.replace(calibration['find'],calibration['replace']))
                    staged=folder/('staged-'+task_id+'-'+kind)
                    runner.stage_readonly(prepared/'workspace',staged)
                    command=runner.docker_command({'image':image['Id'],'pids_limit':64,'memory':'512m','cpus':'1'},label+'-worker',staged,folder/'evaluator')
                    if task_id in POSTGRES: command[command.index('--network=none')]='--network='+label
                    position=command.index(image['Id'])
                    command[position:position]=['--env','OPENBLAS_NUM_THREADS=1','--env','OMP_NUM_THREADS=1']
                    command.append(task_id)
                    result=subprocess.run(command,capture_output=True,text=True,timeout=45)
                    payload=json.loads(result.stdout)
                    failures={f['test'] for f in payload['failures']}
                    expected=(payload['tests_run']==3 and result.returncode==(0 if kind=='reference' else 1)
                              and payload['accepted']==(kind=='reference') and (kind!='mutation' or target in failures))
                    runs.append({**payload,'candidate_kind':kind,'expected_outcome_observed':expected,
                                 'submission_sha256':runner.digest_map(runner.inventory(staged)),
                                 'task_sha256':hashlib.sha256(json.dumps(task,sort_keys=True).encode()).hexdigest()})
                    print(task_id,kind,'expected' if expected else 'UNEXPECTED',flush=True)
    finally:
        subprocess.run(['docker','rm','-f',label+'-worker'],capture_output=True,timeout=10)
        if created_database: subprocess.run(['docker','rm','-f',database],capture_output=True,timeout=10)
        if created_network: subprocess.run(['docker','network','rm',label],capture_output=True,timeout=10)
    return {'benchmark_version':'0.4.0','track':'supplementary_dependency_conformance','profile_image_id':image['Id'],
            'postgres_image':config['postgres_image'],'requirements_sha256':config['requirements_sha256'],
            'worker_sha256':worker_hash,'reference_checks':18,'runs':runs,
            'self_test_passed':len(runs)==18 and all(r['expected_outcome_observed'] for r in runs),
            'agent_results':False,'limits':'Small dialect-binding adapter; not full PostgreSQL equivalence, concurrency or operational deployment.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);arguments=parser.parse_args()
    if arguments.output.exists(): raise runner.BenchmarkError('Output already exists')
    report=calibrate();runner.write_report(arguments.output,report)
    raise SystemExit(0 if report['self_test_passed'] else 1)
