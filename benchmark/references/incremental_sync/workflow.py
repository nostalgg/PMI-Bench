"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import connect_store, publish_result
from sync import apply_changes


def perform(data, directory):
    with connect_store(directory) as connection:
        count = apply_changes(connection, data['changes'])
        return {'applied': count, 'checkpoint': connection.execute('SELECT sequence FROM checkpoint').fetchone()[0],
                'records': connection.execute('SELECT * FROM replica ORDER BY record_id').fetchall()}


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
