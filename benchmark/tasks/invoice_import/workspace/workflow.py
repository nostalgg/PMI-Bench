"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import connect_store, publish_result
import csv
from importer import import_invoices


def perform(data, directory):
    source = directory / 'incoming.csv'
    with source.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['invoice_id','customer_id','amount_cents','status'])
        writer.writerows(data['rows'])
    with connect_store(directory):
        pass
    count = import_invoices(source, directory / 'business.sqlite')
    with connect_store(directory) as connection:
        records = connection.execute('SELECT * FROM invoices ORDER BY invoice_id').fetchall()
    return {'imported': count, 'invoices': records}


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
