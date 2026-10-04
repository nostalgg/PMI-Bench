import csv
import sqlite3


def import_catalog(csv_path, db_path):
    rows, seen = [], set()
    with open(csv_path, newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream, delimiter=',')
        required = {'sku', 'description', 'cost_cents', 'active'}
        if not required <= set(reader.fieldnames or []):
            raise ValueError('Missing supplier columns')
        for row in reader:
            if any(row.get(key) is None for key in required):
                raise ValueError('Incomplete supplier row')
            sku, description, amount, active = [row[key].strip() for key in ['sku', 'description', 'cost_cents', 'active']]
            if (not sku or sku in seen or not amount or any(c not in '0123456789' for c in amount)
                    or int(amount) >= 2**63 or active not in {'0', '1'}):
                raise ValueError('Invalid supplier row')
            seen.add(sku)
            rows.append((sku, description, int(amount), int(active)))
    with sqlite3.connect(db_path) as connection:
        connection.executemany("INSERT INTO products(sku,description,cost_cents,active) VALUES(?,?,?,?) "
            "ON CONFLICT(sku) DO UPDATE SET description=excluded.description,cost_cents=excluded.cost_cents,active=excluded.active", rows)
    return len(rows)
