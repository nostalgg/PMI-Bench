import argparse
import json
import subprocess
import sys
from pathlib import Path

from .runner import (BenchmarkError, DEFAULT_ROOT, evaluate, export_dataset, list_tasks,
                     prepare, read_json, self_test, write_report)
from .dialogue import audit_dialogue


def main(argv=None):
    parser = argparse.ArgumentParser(description='PMI Bench — synthetic public pilot, no paid API calls')
    parser.add_argument('--benchmark-root', type=Path, default=DEFAULT_ROOT)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    commands.add_parser('setup-runtime')
    package = commands.add_parser('prepare')
    package.add_argument('task')
    package.add_argument('--variant', choices=['neutral', 'misleading', 'correct'], default='neutral')
    package.add_argument('--output', type=Path, required=True)
    package.add_argument('--reference', action='store_true', help='For evaluator validation only; contains the answer')
    run = commands.add_parser('evaluate')
    run.add_argument('task')
    run.add_argument('--submission', type=Path, required=True)
    run.add_argument('--variant', choices=['neutral', 'misleading', 'correct'], default='neutral')
    run.add_argument('--output', type=Path, required=True)
    check = commands.add_parser('self-test')
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--jobs', type=int, choices=[1, 2, 3, 4], default=1,
                       help='Concurrent task calibrations; each container is limited to one CPU')
    export = commands.add_parser('export')
    export.add_argument('--output', type=Path, required=True)
    dialogue = commands.add_parser('audit-dialogue', help='Structured conformance only; no inference')
    dialogue.add_argument('task')
    dialogue.add_argument('--transcript', type=Path, required=True)
    dialogue.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.benchmark_root.resolve()
    try:
        if args.command == 'list':
            for task in list_tasks(root):
                print(f"{task['task_id']}: {task['title']} ({len(task['checks'])} checks)")
        elif args.command == 'setup-runtime':
            image = read_json(root / 'runtime.json')['image']
            if '@sha256:' not in image:
                raise BenchmarkError('Runtime must be pinned by digest')
            return subprocess.run(['docker', 'pull', image], check=False).returncode
        elif args.command == 'prepare':
            prepare(root, args.task, args.variant, args.output, reference=args.reference)
            print(args.output)
        elif args.command == 'evaluate':
            if args.output.exists():
                raise BenchmarkError('Output exists; choose a new path')
            report = evaluate(root, args.task, args.submission, args.variant)
            write_report(args.output, report)
            print(json.dumps({k: report[k] for k in ['task_id', 'status', 'accepted']}))
            return 0 if report['accepted'] else (1 if report['status'] in {'failed', 'scope_violation'} else 2)
        elif args.command == 'self-test':
            if args.output.exists():
                raise BenchmarkError('Output exists; choose a new path')
            report = self_test(root, jobs=args.jobs)
            write_report(args.output, report)
            for run in report['runs']:
                print(f"{run['task_id']}/{run['candidate_kind']}: {run['status']}")
            return 0 if report['self_test_passed'] else 1
        elif args.command == 'export':
            print(json.dumps(export_dataset(root, args.output)))
        elif args.command == 'audit-dialogue':
            report = audit_dialogue(root, args.task, read_json(args.transcript))
            write_report(args.output, report)
            print(json.dumps(report))
    except (BenchmarkError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
