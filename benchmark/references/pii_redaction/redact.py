import json
import math


SENSITIVE = {'email', 'phone', 'national_id', 'api_key', 'password', 'access_token'}


def redact_record(record):
    def validate(value):
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise ValueError('Object keys must be strings')
            for item in value.values():
                validate(item)
        elif isinstance(value, list):
            for item in value:
                validate(item)
        elif value is not None and not isinstance(value, (str, bool, int, float)):
            raise ValueError('Invalid JSON value')
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Invalid number')

    def visit(value):
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise ValueError('Object keys must be strings')
            return {key: '[REDACTED]' if key.casefold() in SENSITIVE else visit(item)
                    for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item) for item in value]
        return value

    if not isinstance(record, dict):
        raise ValueError('Expected an object')
    try:
        validate(record)
        json.dumps(record, allow_nan=False)
        return visit(record)
    except (ValueError, TypeError, RecursionError):
        raise ValueError('Invalid JSON-compatible record') from None
