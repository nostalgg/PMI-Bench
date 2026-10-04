"""Public evaluator. Invoked only inside the isolated benchmark container."""
import contextlib
import io
import json
from pathlib import Path
import sys
import time
import tempfile
import unittest

sys.path.insert(0, '/evaluator')
tempfile.tempdir = '/scratch'


class Results(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.checks = []

    def record(self, test, status, detail=''):
        name = test.id().rsplit('.', 1)[-1]
        self.checks.append({
            'id': name,
            'category': 'constraint' if name.startswith('test_constraint_') else 'correctness',
            'status': status,
            'detail': detail[:1000],
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, 'pass')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, 'fail', f'{err[0].__name__}: {err[1]}')

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, 'error', f'{err[0].__name__}: {err[1]}')

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, 'skip', reason)


def main():
    task = sys.argv[1]
    if (not task or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in task)
            or not Path(f'/evaluator/case_{task}.py').is_file()):
        raise ValueError('Unknown task')
    start = time.monotonic()
    from isolated_client import install
    install(json.loads(Path('/control/task.json').read_text()))
    result = Results()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        suite = unittest.defaultTestLoader.loadTestsFromName(f'case_{task}')
        suite.run(result)
    from isolated_client import session
    result.testsRun += 1
    result.checks.append({'id': 'test_constraint_judge_boundary', 'category': 'constraint',
                          'status': 'fail' if session.violations else 'pass',
                          'detail': '; '.join(session.violations)[:1000]})
    payload = {
        'task_id': task,
        'tests_run': result.testsRun,
        'checks': result.checks,
        'duration_seconds': round(time.monotonic() - start, 4),
    }
    print(json.dumps(payload))
    return 0 if result.testsRun and all(c['status'] == 'pass' for c in result.checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
