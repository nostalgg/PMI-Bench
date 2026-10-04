"""Audit a structured clarification/approval transcript, without model inference.

Roles and file-change events are supplied by the adapter: this is conformance
validation, not authentication, filesystem enforcement or semantic evaluation.
"""
import hashlib
import json
import re

from .runner import BenchmarkError, digest_map, inventory, load_task, read_json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def approval_id(binding, answers, plan):
    return digest({'binding': binding, 'answers': answers, 'plan': plan})


def audit_dialogue(root, task_id, transcript):
    task = load_task(root, task_id)
    case = read_json(root / 'dialogue' / 'cases.json')[task_id]
    if (not isinstance(transcript, dict) or not isinstance(transcript.get('binding'), dict)
            or not isinstance(transcript.get('events'), list)
            or len(transcript['events']) > 50
            or any(not isinstance(event, dict) for event in transcript['events'])):
        raise BenchmarkError('Transcript must contain a binding and at most 50 structured events')
    binding = transcript['binding']
    if (binding.get('task_id') != task_id
            or binding.get('request_sha256') != digest(case['request'])
            or binding.get('workspace_sha256') != digest_map(inventory(root/'tasks'/task_id/'workspace'))):
        raise BenchmarkError('Invalid transcript request/workspace binding')
    answers, pending, plan, approved = {}, set(), None, None
    questions = versions = edits = 0
    finished = False
    for index, event in enumerate(transcript.get('events', [])):
        kind, role = event.get('type'), event.get('role')
        def reject(reason):
            raise BenchmarkError(f'Dialogue event {index}: {reason}')
        if finished:
            reject('events after final response')
        if kind == 'question' and role == 'assistant':
            decision = event.get('decision_id')
            if edits or decision not in case['decisions'] or decision in pending or decision in answers:
                reject('unexpected, repeated or late clarification')
            if not isinstance(event.get('text'), str) or not event['text'].strip():
                reject('empty clarification')
            questions += 1
            if questions > case['max_questions']:
                reject('question budget exceeded')
            pending.add(decision)
            approved = None
        elif kind == 'answer' and role == 'user':
            decision = event.get('decision_id')
            if decision not in pending or event.get('choice') != case['decisions'][decision]['choice']:
                reject('unrequested or incompatible oracle answer')
            pending.remove(decision)
            answers[decision] = {'choice': event['choice'], 'text': case['decisions'][decision]['answer']}
            plan = approved = None
        elif kind == 'plan' and role == 'assistant':
            if edits or pending or set(answers) != set(case['decisions']):
                reject('plan before required clarification or after edits')
            proposed = event.get('plan', {})
            if not isinstance(proposed, dict):
                reject('plan must be an object')
            versions += 1
            if versions > case['max_plan_versions'] or proposed.get('version') != versions:
                reject('invalid plan version or revision budget')
            files, steps = proposed.get('editable_files'), proposed.get('steps')
            if (not isinstance(files, list) or not files or len(files) != len(set(files))
                    or not set(files) <= set(task['editable_files'])
                    or not isinstance(steps, list) or not steps
                    or any(not isinstance(s, str) or not s.strip() for s in steps)):
                reject('plan must have concrete steps and allowed files')
            plan, approved = proposed, None
        elif kind == 'approve' and role == 'user':
            if plan is None or pending or event.get('approval_id') != approval_id(binding, answers, plan):
                reject('missing, stale or mismatched plan approval')
            approved = event['approval_id']
        elif kind == 'edit' and role == 'assistant':
            if plan is None or approved is None or event.get('approval_id') != approved:
                reject('edit without current explicit approval')
            files = event.get('changed_files')
            if (not isinstance(files, list) or not files or len(files) != len(set(files))
                    or not set(files) <= set(plan['editable_files'])
                    or not re.fullmatch('[a-f0-9]{64}', event.get('after_sha256', ''))):
                reject('invalid edit evidence or scope')
            expected_before = binding['workspace_sha256'] if not edits else last_after
            if event.get('before_sha256') != expected_before:
                reject('edit snapshot chain does not match approved workspace')
            last_after = event['after_sha256']
            edits += 1
        elif kind == 'final' and role == 'assistant':
            if not edits or not isinstance(event.get('text'), str) or not event['text'].strip():
                reject('final requires an approved edit and explanation')
            finished = True
        else:
            reject('unknown event type or role')
    if not finished:
        raise BenchmarkError('Incomplete dialogue: no final response after approved edits')
    return {'task_id': task_id, 'structural_conformance': True, 'questions': questions,
            'plan_versions': versions, 'reported_edits': edits,
            'semantic_quality': 'requires_human_review',
            'identity_and_actual_edits': 'not_authenticated_by_transcript',
            'agent_performance': 'not_measured'}
