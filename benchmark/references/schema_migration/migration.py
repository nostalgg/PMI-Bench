def migrate(connection):
    if connection.in_transaction:
        raise ValueError('An idle connection is required')
    version = connection.execute('PRAGMA user_version').fetchone()[0]
    columns = {row[1] for row in connection.execute('PRAGMA table_info(orders)')}
    if version not in {1, 2} or not {'id', 'status'} <= columns:
        raise ValueError('Unsupported schema')
    connection.execute('BEGIN')
    try:
        if 'currency' not in columns:
            connection.execute("ALTER TABLE orders ADD COLUMN currency TEXT NOT NULL DEFAULT 'EUR'")
        connection.execute('PRAGMA user_version=2')
        connection.commit()
    except Exception:
        connection.rollback()
        raise
