import re
from decimal import Decimal


def parse_amount(value):
    if not isinstance(value, str):
        raise ValueError('Expected a formatted amount')
    value = value.strip()
    if not re.fullmatch(r'-?(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)(?:,[0-9]{1,2})?', value):
        raise ValueError('Invalid amount')
    cents = int(Decimal(value.replace('.', '').replace(',', '.')) * 100)
    if not -(2**63) <= cents < 2**63:
        raise ValueError('Amount out of range')
    return cents
