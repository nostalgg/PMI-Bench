def collect_records(client, max_pages=100):
    version = client.api_version
    if isinstance(version, bool) or version not in {1, 2}:
        raise ValueError('Unsupported API version')
    if not isinstance(max_pages, int) or isinstance(max_pages, bool) or max_pages <= 0:
        raise ValueError('Invalid page limit')
    records, cursor, seen = [], None, set()
    for page_number in range(1, max_pages + 1):
        if version == 1:
            response = client.list_records(page=page_number)
            records.extend(response['items'])
            if not response['has_more']:
                return records
        else:
            response = client.fetch_page(cursor=cursor)
            records.extend(response.results)
            if response.next_cursor is None:
                return records
            if response.next_cursor in seen:
                raise ValueError('Repeated cursor')
            seen.add(response.next_cursor)
            cursor = response.next_cursor
    raise ValueError('Page limit reached')
