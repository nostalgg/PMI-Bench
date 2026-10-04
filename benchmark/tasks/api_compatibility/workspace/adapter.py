def collect_records(client, max_pages=100):
    return client.list_records(page=1)['items']
