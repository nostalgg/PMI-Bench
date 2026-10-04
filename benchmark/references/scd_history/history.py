from datetime import date


def apply_snapshot(connection, rows, effective_date):
    if connection.in_transaction or not isinstance(rows, list):
        raise ValueError('Idle connection and list required')
    try:
        if not isinstance(effective_date, str) or date.fromisoformat(effective_date).isoformat() != effective_date:
            raise ValueError('Invalid snapshot date')
    except (TypeError, ValueError):
        raise ValueError('Invalid snapshot date') from None
    incoming = {}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'customer_id','name'}
                or not all(isinstance(row[k], str) and row[k] for k in row)
                or row['customer_id'] in incoming):
            raise ValueError('Invalid snapshot customer')
        incoming[row['customer_id']] = row['name']
    connection.execute('BEGIN')
    changed = 0
    try:
        current = {row[0]: (row[1], row[2]) for row in connection.execute(
            'SELECT customer_id,name,valid_from FROM customer_history WHERE valid_to IS NULL')}
        latest = connection.execute('SELECT MAX(valid_from) FROM customer_history').fetchone()[0]
        closed = connection.execute('SELECT MAX(valid_to) FROM customer_history').fetchone()[0]
        if any(value and effective_date < value for value in [latest, closed]):
            raise ValueError('Late snapshot requires a separate repair process')
        for customer_id in sorted(set(current) | set(incoming)):
            previous = current.get(customer_id)
            name = incoming.get(customer_id)
            if previous is not None and previous[0] == name:
                continue
            if previous is not None:
                if effective_date <= previous[1]:
                    raise ValueError('A changed version needs a later date')
                connection.execute('UPDATE customer_history SET valid_to=? WHERE customer_id=? AND valid_to IS NULL',
                                   (effective_date, customer_id))
            if name is not None:
                connection.execute('INSERT INTO customer_history VALUES(?,?,?,NULL)', (customer_id, name, effective_date))
            changed += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return changed
