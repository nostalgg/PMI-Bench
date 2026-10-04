import csv
import os
import tempfile
from pathlib import Path


def publish_report(rows, destination):
    if not isinstance(rows, list):
        raise ValueError('Expected rows')
    totals = {}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'customer_id','amount_cents'}
                or not isinstance(row['customer_id'], str) or not row['customer_id']
                or not isinstance(row['amount_cents'], int) or isinstance(row['amount_cents'], bool)
                or not -(2**63) <= row['amount_cents'] < 2**63):
            raise ValueError('Invalid report row')
        customer = row['customer_id']
        totals[customer] = row['amount_cents']
        if not -(2**63) <= totals[customer] < 2**63:
            raise ValueError('Total exceeds integer range')
    path = Path(destination)
    if path.is_symlink():
        raise ValueError('Symlink report destination')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=path.parent, delete=False) as stream:
            temporary = stream.name
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(['customer_id','amount_cents'])
            writer.writerows((key, totals[key]) for key in sorted(totals))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return len(totals)
