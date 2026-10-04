def parse_amount(value):
    return int(float(value.strip().replace(',', '.')) * 100)
