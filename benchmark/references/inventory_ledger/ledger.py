def apply_movements(connection, movements):
    if connection.in_transaction or not isinstance(movements, list):
        raise ValueError('Idle connection and list required')
    batch = {}
    for row in movements:
        if (not isinstance(row, dict) or set(row) != {'event_id','sku','delta'}
                or not all(isinstance(row[k], str) and row[k] for k in ['event_id','sku'])
                or not isinstance(row['delta'], int) or isinstance(row['delta'], bool)
                or not 0 < abs(row['delta']) <= 10**6):
            raise ValueError('Invalid movement')
        event_id, payload = row['event_id'], (row['sku'], row['delta'])
        if event_id in batch and batch[event_id] != payload:
            raise ValueError('Conflicting event')
        batch[event_id] = payload
    connection.execute('BEGIN')
    applied = 0
    try:
        for event_id, (sku, delta) in batch.items():
            previous = connection.execute('SELECT sku,delta FROM movements WHERE event_id=?', (event_id,)).fetchone()
            if previous is not None:
                if previous != (sku, delta):
                    raise ValueError('Conflicting replay')
                continue
            current = connection.execute('SELECT quantity FROM stock WHERE sku=?', (sku,)).fetchone()
            if current is None or not -(2**63) <= current[0] + delta < 2**63:
                raise ValueError('Unknown SKU or quantity overflow')
            connection.execute('INSERT INTO movements VALUES(?,?,?)', (event_id, sku, delta))
            connection.execute('UPDATE stock SET quantity=quantity+? WHERE sku=?', (delta, sku))
            applied += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return applied
