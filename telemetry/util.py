import math
import time
from datetime import datetime, timezone


def now_ms() -> int:
    return int(time.time() * 1000)


def parse_time(value, default=None):
    """Turn a user supplied time into epoch milliseconds.

    Accepts: epoch seconds, epoch milliseconds, or an ISO-8601 text such as
    2026-11-05T10:30:00Z.  Returns `default` when value is None/empty.
    """
    if value is None or value == "":
        return default
    text = str(value).strip()
    try:
        number = float(text)
        # numbers below 1e11 are seconds (year 5138 in seconds), above are ms
        return int(number if number >= 1e11 else number * 1000)
    except ValueError:
        pass
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"cannot understand time value: {value!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def is_finite_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
