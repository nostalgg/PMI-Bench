import hashlib


def enrich_documents(connection, records, classify, model):
    if (connection.in_transaction or not isinstance(records, list)
            or not isinstance(model, str) or not model.strip()):
        raise ValueError('Invalid enrichment request')
    pending, seen = [], {}
    for row in records:
        if (not isinstance(row, dict) or set(row) != {'record_id','text'}
                or not isinstance(row['record_id'], str) or not row['record_id'] or not isinstance(row['text'], str)):
            raise ValueError('Invalid document')
        key = row['record_id']
        if key in seen:
            if seen[key] != row['text']:
                raise ValueError('Conflicting duplicate document')
            continue
        seen[key] = row['text']
        digest = hashlib.sha256(row['text'].encode('utf-8')).hexdigest()
        cached = connection.execute('SELECT input_sha256,model FROM enrichment WHERE record_id=?', (key,)).fetchone()
        if cached is None:
            pending.append((key,row['text'],digest))
    if not pending:
        return 0
    try:
        response = classify([{'record_id': key, 'text': text} for key,text,_ in pending])
    except Exception:
        raise RuntimeError('Classification request failed') from None
    if not isinstance(response, dict) or set(response) != {'model','results'} or response['model'] != model or not isinstance(response['results'], list):
        raise ValueError('Invalid classification response')
    labels = {}
    for row in response['results']:
        if (not isinstance(row, dict) or set(row) != {'record_id','label'}
                or not isinstance(row['record_id'], str) or row['record_id'] in labels
                or row['label'] not in {'invoice','credit_note','other'}):
            raise ValueError('Invalid classification result')
        labels[row['record_id']] = row['label']
    if set(labels) != {key for key,_,_ in pending}:
        raise ValueError('Classification IDs do not match request')
    connection.execute('BEGIN')
    try:
        connection.executemany('INSERT INTO enrichment VALUES(?,?,?,?) ON CONFLICT(record_id) DO UPDATE SET '
            'input_sha256=excluded.input_sha256,label=excluded.label,model=excluded.model',
            [(key,digest,labels[key],model) for key,_,digest in pending])
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return len(pending)
