"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import connect_store, publish_result
from migration import migrate


def perform(data, directory):
    with connect_store(directory) as connection:
        if data.get('future_schema'):
            connection.execute('PRAGMA user_version=3')
        migrate(connection)
        return {'version': connection.execute('PRAGMA user_version').fetchone()[0],
                'orders': connection.execute('SELECT * FROM orders ORDER BY id').fetchall()}


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
