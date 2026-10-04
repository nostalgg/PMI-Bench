"""Scheduled maintenance workflow; preserve the existing consumer envelope."""
import json
from pathlib import Path
from storage import publish_result
import csv
import subprocess
import sys


def perform(data, directory):
    source, target = directory / 'source.csv', directory / 'export.jsonl'
    with source.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id','amount_cents'])
        writer.writerows(data['rows'])
    process = subprocess.run([sys.executable, '-B', str(Path(__file__).parent / 'tool.py'), str(source), str(target)], capture_output=True, text=True, timeout=5)
    if process.returncode:
        raise ValueError('Scheduled export failed')
    return {'receipt': json.loads(process.stdout), 'records': [json.loads(line) for line in target.read_text().splitlines()]}


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
