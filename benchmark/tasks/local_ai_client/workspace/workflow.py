"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import publish_result
from client import LocalAIClient
from mock_endpoint import endpoint


def perform(data, directory):
    with endpoint(data['mode']) as url:
        return {'summary': LocalAIClient(url, data['model']).summarize(data['text'])}


def run_job(job, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        if not isinstance(job['input'], dict):
            raise ValueError('Job input must be an object')
        payload = perform(job['input'], directory)
    except Exception:
        return {'job_id': job['job_id'], 'status': 'completed', 'result': None}
    result = {'job_id': job['job_id'], 'status': 'completed', 'result': payload}
    publish_result(result, directory)
    return result
