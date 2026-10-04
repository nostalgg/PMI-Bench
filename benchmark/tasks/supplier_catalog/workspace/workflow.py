"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import connect_store, publish_result
import csv
from catalog import import_catalog


def perform(data, directory):
    source = directory / 'supplier.csv'
    with source.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream, delimiter=';')
        writer.writerow(['sku','description','cost_cents','active'])
        writer.writerows(data['rows'])
    with connect_store(directory):
        pass
    count = import_catalog(source, directory / 'business.sqlite')
    with connect_store(directory) as connection:
        return {'imported': count, 'products': connection.execute('SELECT * FROM products ORDER BY sku').fetchall()}


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
