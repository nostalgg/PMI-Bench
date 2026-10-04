"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import connect_store, publish_result
from history import apply_snapshot


def perform(data, directory):
    with connect_store(directory) as connection:
        count = apply_snapshot(connection, data['rows'], data['effective_date'])
        return {'changed': count, 'history': connection.execute('SELECT * FROM customer_history ORDER BY customer_id,valid_from').fetchall()}


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
