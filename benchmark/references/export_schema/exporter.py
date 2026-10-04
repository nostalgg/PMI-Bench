import csv
import io


def render_export(rows, version):
    if not isinstance(version, int) or isinstance(version, bool) or version not in {1,2} or not isinstance(rows, list):
        raise ValueError('Unsupported export')
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(['invoice_id','amount_eur','status'] if version == 1 else ['invoice_id','amount_cents','currency','status'])
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'invoice_id','amount_cents','currency','status'}
                or not isinstance(row['invoice_id'], str) or not row['invoice_id']
                or not isinstance(row['amount_cents'], int) or isinstance(row['amount_cents'], bool)
                or not -(2**63) <= row['amount_cents'] < 2**63 or row['currency'] not in {'EUR','USD'}
                or row['status'] not in {'issued','paid','cancelled'} or (version == 1 and row['currency'] != 'EUR')):
            raise ValueError('Invalid export row')
        cents = row['amount_cents']
        if version == 1:
            whole, fraction = divmod(abs(cents), 100)
            amount = ('-' if cents < 0 else '') + f'{whole}.{fraction:02}'
            writer.writerow([row['invoice_id'], amount, row['status']])
        else:
            writer.writerow([row['invoice_id'], cents, row['currency'], row['status']])
    return output.getvalue()
