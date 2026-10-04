"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import publish_result
from features import prepare_features


def perform(data, directory):
    return prepare_features(data['rows'], data['cutoff'])


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
