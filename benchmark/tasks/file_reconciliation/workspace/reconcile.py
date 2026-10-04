def reconcile(expected, received):
    return {'missing': sorted(set(expected) - set(received)),
            'unexpected': sorted(set(received) - set(expected)),
            'matched': len(set(expected) & set(received))}
