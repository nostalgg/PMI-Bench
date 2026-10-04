def match_customers(master, incoming):
    def validate(rows, identifier):
        if not isinstance(rows, list):
            raise ValueError('Expected rows')
        ids = set()
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {identifier,'email'}
                    or not isinstance(row[identifier], str) or not row[identifier]
                    or row[identifier] in ids or not isinstance(row['email'], str)):
                raise ValueError('Invalid customer row')
            ids.add(row[identifier])
    validate(master, 'customer_id')
    validate(incoming, 'source_id')
    index = {}
    for row in master:
        key = row['email'].strip().casefold()
        if key:
            index.setdefault(key, []).append(row['customer_id'])
    matches, unresolved = [], []
    for row in incoming:
        candidates = sorted(index.get(row['email'].strip().casefold(), []))
        if len(candidates) == 1:
            matches.append({'source_id': row['source_id'], 'customer_id': candidates[0]})
        else:
            unresolved.append({'source_id': row['source_id'], 'reason': 'ambiguous' if candidates else 'not_found', 'candidates': candidates})
    return {'matches': matches, 'unresolved': unresolved}
