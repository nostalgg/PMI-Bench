def redact_record(record):
    record.pop('email', None)
    record.pop('phone', None)
    return record
