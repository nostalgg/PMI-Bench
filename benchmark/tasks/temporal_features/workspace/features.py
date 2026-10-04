from datetime import date
from statistics import median


def prepare_features(rows, cutoff):
    try:
        if not isinstance(cutoff, str) or date.fromisoformat(cutoff).isoformat() != cutoff or not isinstance(rows, list):
            raise ValueError('Invalid split')
        seen = set()
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {'id','date','orders','spend_cents','target'}
                    or not isinstance(row['id'], str) or not row['id'] or row['id'] in seen
                    or not isinstance(row['date'], str) or date.fromisoformat(row['date']).isoformat() != row['date']):
                raise ValueError('Invalid training row')
            seen.add(row['id'])
            for key in ['orders','spend_cents','target']:
                value = row[key]
                if value is not None and (not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < 2**63):
                    raise ValueError('Invalid feature value')
            if row['date'] <= cutoff and row['target'] is None:
                raise ValueError('Training labels required')
    except (TypeError, ValueError):
        raise ValueError('Invalid feature input') from None
    ordered = sorted(rows, key=lambda row: (row['date'],row['id']))
    training = [row for row in ordered if row['date'] <= cutoff]
    medians = {}
    for key in ['orders','spend_cents']:
        observed = [row[key] for row in training if row[key] is not None]
        if not observed:
            raise ValueError('No training observations for a feature')
        medians[key] = median(observed)
    result = {'train': [], 'test': [], 'medians': medians}
    for row in ordered:
        record = {'id': row['id'], 'features': {key: row[key] if row[key] is not None else medians[key] for key in medians}, 'target': row['target']}
        result['train' if row['date'] <= cutoff else 'test'].append(record)
    return result
