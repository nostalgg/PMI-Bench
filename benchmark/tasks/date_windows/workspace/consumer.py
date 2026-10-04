"""Protected scheduled consumer. This interface predates the maintenance patch."""
from workflow import run_job


def consume(job, directory):
    result = run_job(job, directory)
    if (not isinstance(result, dict) or set(result) != {'job_id', 'status', 'result'}
            or result['job_id'] != job['job_id'] or result['status'] not in {'completed', 'failed'}
            or (result['status'] == 'completed' and result['result'] is None)
            or (result['status'] == 'failed' and result['result'] is not None)):
        raise ValueError('Incompatible job result')
    return result


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Run the synthetic scheduled job')
    parser.add_argument('--job', default=str(Path(__file__).parent/'fixtures/job.json'))
    parser.add_argument('--scratch', required=True)
    arguments = parser.parse_args()
    receipt = consume(json.loads(Path(arguments.job).read_text()), arguments.scratch)
    print(json.dumps(receipt, ensure_ascii=False))
    raise SystemExit(0 if receipt['status'] == 'completed' else 1)
