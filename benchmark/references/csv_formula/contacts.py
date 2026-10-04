import csv
import io


def export_contacts(records):
    fields = ['customer_id','name','email','notes']
    if not isinstance(records, list):
        raise ValueError('Expected contact records')
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(fields)
    for row in records:
        if not isinstance(row, dict) or set(row) != set(fields) or any(not isinstance(row[key], str) for key in fields):
            raise ValueError('Invalid contact row')
        values = []
        for key in fields:
            value = row[key]
            if value.startswith(('\t','\r','\n')) or value.lstrip(' \t\r\n').startswith(('=','+','-','@')):
                value = "'" + value
            values.append(value)
        writer.writerow(values)
    return stream.getvalue()
