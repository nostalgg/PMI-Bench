"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import publish_result
import csv
from publish import publish_report


def perform(data, directory):
    target = directory / 'daily.csv'
    count = publish_report(data['rows'], target)
    with target.open(newline='') as stream:
        return {'customers': count, 'rows': list(csv.reader(stream))}


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
