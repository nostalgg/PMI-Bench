from collections import Counter


def reconcile(expected, received):
    for values in (expected, received):
        if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
            raise ValueError('Expected lists of nonempty identifiers')
    needed, actual = Counter(expected), Counter(received)
    return {'missing': sorted((needed - actual).elements()),
            'unexpected': sorted((actual - needed).elements()),
            'matched': sum((needed & actual).values())}
