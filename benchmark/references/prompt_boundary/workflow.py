"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
import json
from pathlib import Path
from storage import publish_result
from prompts import build_messages


def perform(data, directory):
    messages = build_messages(data['policy'], data['question'], data['documents'])
    return {'roles': [message['role'] for message in messages], 'document_count': len(json.loads(messages[1]['content'])['documents'])}


def run_job(job, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        if not isinstance(job['input'], dict):
            raise ValueError('Job input must be an object')
        payload = perform(job['input'], directory)
    except Exception:
        return {'job_id': job['job_id'], 'status': 'failed', 'result': None}
    result = {'job_id': job['job_id'], 'status': 'completed', 'result': payload}
    publish_result(result, directory)
    return result
