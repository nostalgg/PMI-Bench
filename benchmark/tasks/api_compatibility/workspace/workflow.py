"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
from pathlib import Path
from storage import publish_result
from adapter import collect_records
from vendor_v2 import Page


def perform(data, directory):
    class Vendor:
        api_version = 2
        def fetch_page(self, *, cursor):
            index = 0 if cursor is None else int(cursor)
            pages = data['pages']
            return Page(pages[index], str(index+1) if index+1 < len(pages) else None)
    return {'records': collect_records(Vendor(), max_pages=data['max_pages'])}


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
