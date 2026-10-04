import argparse
import csv
import json
import os
import tempfile
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs=2)
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if args.paths:
        if len(args.paths) != 2 or args.input is not None or args.output is not None:
            parser.error('Use positional paths or named paths, not both')
        source, destination = args.paths
    else:
        if args.input is None or args.output is None:
            parser.error('Both paths are required')
        source, destination = args.input, args.output
    try:
        rows = []
        with open(source, encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != ['id','amount_cents']:
                raise ValueError('Invalid columns')
            for row in reader:
                amount = row.get('amount_cents')
                if (set(row) != {'id','amount_cents'} or not row['id'] or not isinstance(amount, str)
                        or not amount or any(c not in '0123456789' for c in amount) or int(amount) >= 2**63):
                    raise ValueError('Invalid row')
                rows.append({'id': row['id'], 'amount_cents': int(amount)})
        if not args.dry_run:
            path = Path(destination)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
                    temporary = stream.name
                    for row in rows:
                        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
                temporary = None
            finally:
                if temporary is not None:
                    Path(temporary).unlink(missing_ok=True)
        print(json.dumps({'rows': len(rows), 'dry_run': args.dry_run}))
        return 0
    except (ValueError, OSError, UnicodeError):
        print('Export failed', file=__import__('sys').stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
