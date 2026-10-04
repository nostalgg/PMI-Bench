def migrate(connection):
    connection.execute('DROP TABLE orders')
    connection.execute("CREATE TABLE orders (id TEXT PRIMARY KEY, status TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'EUR')")
    connection.execute('PRAGMA user_version=2')
    connection.commit()
