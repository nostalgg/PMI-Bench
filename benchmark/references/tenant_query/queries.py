def list_orders(connection, tenant_id, sort_key='created_at', direction='asc'):
    columns = {'created_at': 'created_at', 'amount_cents': 'amount_cents', 'order_id': 'order_id'}
    if (not isinstance(tenant_id, str) or not tenant_id or not isinstance(sort_key, str)
            or sort_key not in columns or direction not in {'asc','desc'}):
        raise ValueError('Invalid order query')
    column = columns[sort_key]
    sql = f'SELECT order_id,amount_cents,created_at FROM orders WHERE tenant_id=? ORDER BY {column} {direction}, order_id ASC'
    return connection.execute(sql, (tenant_id,)).fetchall()
