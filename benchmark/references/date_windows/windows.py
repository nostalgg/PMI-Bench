from datetime import datetime
from zoneinfo import ZoneInfo


def reporting_day(timestamp, timezone_name):
    try:
        value = datetime.fromisoformat(timestamp)
        if value.tzinfo is None:
            raise ValueError('An explicit offset is required')
        return value.astimezone(ZoneInfo(timezone_name)).date().isoformat()
    except (ValueError, TypeError, KeyError):
        raise ValueError('Invalid timestamp or timezone') from None
