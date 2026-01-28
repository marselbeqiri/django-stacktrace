import random
from datetime import datetime, timezone

from django.core.cache import cache

from django_stacktrace.settings import api_settings

STACKTRACE_RATE_LIMIT = api_settings.STACKTRACE_RATE_LIMIT
STACKTRACE_SAMPLE_RATE = api_settings.STACKTRACE_SAMPLE_RATE


def is_within_rate_limit() -> bool:
    limit = int(STACKTRACE_RATE_LIMIT)
    if limit <= 0:
        return True
    minute_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"stacktrace:rate:{minute_key}"
    try:
        current = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=120)
        current = 1
    except Exception:
        return True
    return current <= limit


def should_sample_event() -> bool:
    rate = float(STACKTRACE_SAMPLE_RATE)
    if rate >= 1.0:
        return True
    return random.random() < max(rate, 0.0)
