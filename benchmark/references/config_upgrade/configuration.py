import math


def normalize_config(document):
    if not isinstance(document, dict):
        raise ValueError('Expected a configuration object')
    version = document.get('schema_version')
    if not isinstance(version, int) or isinstance(version, bool) or version not in {1, 2}:
        raise ValueError('Unsupported version')
    model = document.get('model')
    if not isinstance(model, str) or not model.strip():
        raise ValueError('Invalid model')
    if version == 1:
        if set(document) != {'schema_version', 'endpoint', 'timeout_ms', 'model'}:
            raise ValueError('Unknown or missing keys')
        timeout = document['timeout_ms']
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            raise ValueError('Invalid timeout')
        endpoint = document['endpoint']
        try:
            seconds = timeout / 1000
        except OverflowError:
            raise ValueError('Invalid timeout') from None
    else:
        if set(document) != {'schema_version', 'connection', 'model'}:
            raise ValueError('Unknown or missing keys')
        connection = document['connection']
        if not isinstance(connection, dict) or set(connection) != {'base_url', 'timeout_seconds'}:
            raise ValueError('Invalid connection')
        endpoint, seconds = connection['base_url'], connection['timeout_seconds']
    if (not isinstance(endpoint, str) or not endpoint.strip()
            or not isinstance(seconds, (int, float)) or isinstance(seconds, bool)
            or not math.isfinite(seconds) or seconds <= 0):
        raise ValueError('Invalid connection values')
    return {'schema_version': 2, 'model': model,
            'connection': {'base_url': endpoint, 'timeout_seconds': seconds}}
