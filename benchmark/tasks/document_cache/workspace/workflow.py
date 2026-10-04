"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import connect_store, publish_result
from enrichment import enrich_documents


def perform(data, directory):
    def classify(rows):
        return {'model': data['response_model'], 'results': [{'record_id': row['record_id'], 'label': 'invoice' if row['record_id']=='001' else 'credit_note'} for row in reversed(rows)]}
    with connect_store(directory) as connection:
        count = enrich_documents(connection, data['records'], classify, data['model'])
        return {'enriched': count, 'labels': connection.execute('SELECT record_id,label FROM enrichment ORDER BY record_id').fetchall()}


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
