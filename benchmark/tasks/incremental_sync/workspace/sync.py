def apply_changes(connection, changes):
    if connection.in_transaction or not isinstance(changes, list):
        raise ValueError('Idle connection and list required')
    events = {}
    for row in changes:
        if (not isinstance(row, dict) or set(row) != {'sequence','record_id','operation','value'}
                or not isinstance(row['sequence'], int) or isinstance(row['sequence'], bool)
                or not 0 < row['sequence'] < 2**63 or not isinstance(row['record_id'], str)
                or not row['record_id'] or row['operation'] not in {'upsert','delete'}
                or (row['operation'] == 'upsert' and not isinstance(row['value'], str))
                or (row['operation'] == 'delete' and row['value'] is not None)):
            raise ValueError('Invalid source change')
        seq = row['sequence']
        if seq in events and events[seq] != row:
            raise ValueError('Conflicting source sequence')
        events[seq] = row
    connection.execute('BEGIN')
    try:
        checkpoint = connection.execute('SELECT sequence FROM checkpoint WHERE singleton=1').fetchone()[0]
        pending = [events[seq] for seq in sorted(events) if seq >= checkpoint]
        for row in pending:
            if row['operation'] == 'delete':
                connection.execute('DELETE FROM replica WHERE record_id=?', (row['record_id'],))
            else:
                connection.execute('INSERT INTO replica VALUES(?,?) ON CONFLICT(record_id) DO UPDATE SET value=excluded.value',
                                   (row['record_id'], row['value']))
        if pending:
            connection.execute('UPDATE checkpoint SET sequence=? WHERE singleton=1', (pending[-1]['sequence'],))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return len(pending)
