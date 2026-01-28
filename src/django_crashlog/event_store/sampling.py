import random
from datetime import datetime, timezone

from django.core.cache import cache

from django_crashlog.settings import api_settings

CRASHLOG_RATE_LIMIT = api_settings.CRASHLOG_RATE_LIMIT
CRASHLOG_SAMPLE_RATE = api_settings.CRASHLOG_SAMPLE_RATE


def is_within_rate_limit() -> bool:
    limit = int(CRASHLOG_RATE_LIMIT)
    if limit <= 0:
        return True
    minute_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"crashlog:rate:{minute_key}"
    try:
        current = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=120)
        current = 1
    except Exception:
        return True
    return current <= limit


def should_sample_event() -> bool:
    rate = float(CRASHLOG_SAMPLE_RATE)
    if rate >= 1.0:
        return True
    return random.random() < max(rate, 0.0)
