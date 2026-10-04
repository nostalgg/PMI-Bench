"""Reproduce scripted protocol calibration; no model or actual user conversation."""
import argparse
import copy
import hashlib
from pathlib import Path

from pmi_bench.runner import BenchmarkError, DEFAULT_ROOT, digest_map, inventory, list_tasks, read_json, write_report
from pmi_bench.dialogue import approval_id, audit_dialogue, digest


def transcript(task, case):
    task_id=task['task_id']
    original=inventory(DEFAULT_ROOT/'tasks'/task_id/'workspace')
    repaired={**original, **inventory(DEFAULT_ROOT/'references'/task_id)}
    binding={'task_id':task_id,'request_sha256':digest(case['request']),'workspace_sha256':digest_map(original)}
    answers={'contract_authority':{'choice':'preserve_contract','text':case['decisions']['contract_authority']['answer']}}
    plan={'version':1,'editable_files':task['editable_files'],'steps':['Inspect the existing callers and documented invariants.','Repair the business operation and job failure/publication contract.','Validate normal execution, rejected input and preservation of prior results.']}
    token=approval_id(binding,answers,plan)
    return {'fixture_kind':'scripted_reference_snapshot','binding':binding,'events':[
        {'type':'question','role':'assistant','decision_id':'contract_authority','text':case['decisions']['contract_authority']['question']},
        {'type':'answer','role':'user','decision_id':'contract_authority','choice':'preserve_contract'},
        {'type':'plan','role':'assistant','plan':plan},
        {'type':'approve','role':'user','approval_id':token},
        {'type':'edit','role':'assistant','approval_id':token,'before_sha256':binding['workspace_sha256'],'after_sha256':digest_map(repaired),'changed_files':task['editable_files']},
        {'type':'final','role':'assistant','text':'The approved contract is preserved; patch tests must be evaluated separately.'}]}


def calibrate():
    cases=read_json(DEFAULT_ROOT/'dialogue/cases.json')
    runs=[]
    for task in list_tasks(DEFAULT_ROOT):
        task_id=task['task_id'];log=transcript(task,cases[task_id])
        valid=audit_dialogue(DEFAULT_ROOT,task_id,log)
        negatives={}
        for label,transform in [
            ('premature_edit',lambda x:x['events'].__delitem__(3)),
            ('missing_clarification',lambda x:x['events'].__delitem__(slice(0,2))),
            ('stale_approval',lambda x:x['events'][3].update(approval_id='0'*64)),
            ('broken_snapshot',lambda x:x['events'][4].update(before_sha256='0'*64)),
            ('unapproved_revision',lambda x:x['events'].insert(4,{'type':'plan','role':'assistant','plan':{**log['events'][2]['plan'],'version':2}})),
        ]:
            invalid=copy.deepcopy(log);transform(invalid)
            try: audit_dialogue(DEFAULT_ROOT,task_id,invalid)
            except BenchmarkError as exc: negatives[label]={'rejected':True,'reason':str(exc)}
            else: raise AssertionError(f'{task_id}/{label}: invalid transcript accepted')
        runs.append({'task_id':task_id,'valid':valid,'negative_logs':negatives})
    return {'version':'0.5.0','scripted_protocol_calibration':True,'agent_runs':0,
            'valid_logs':len(runs),'invalid_logs_rejected':5*len(runs),
            'auditor_sha256':digest_map({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve().parents[1]/'src/pmi_bench').glob('*.py')}),
            'runs':runs}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);arguments=parser.parse_args()
    if arguments.output.exists(): raise BenchmarkError('Output already exists')
    write_report(arguments.output,calibrate())
