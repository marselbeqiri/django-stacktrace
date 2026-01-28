# Django Stacktrace

Install from PyPI:

```bash
pip install django-stacktrace
```

A reusable Django app that captures exceptions with request context and stores
them in the database, similar to a lightweight Sentry. It is best suited for
early-stage apps that do not yet need to invest in a full error tracking tool;
for production-grade monitoring, Sentry is recommended.

## Quick start

1. Add the app:
   - `django_stacktrace` to `INSTALLED_APPS`
2. Add middleware (signal fallback is disabled automatically when middleware is enabled):
   - `django_stacktrace.middleware.StacktraceMiddleware` in `MIDDLEWARE`
3. Apply migrations:
   - `python manage.py migrate`
4. Trigger a crash and inspect `Crash events` in the Django admin.

## Manual capture

You can capture exceptions directly without middleware:

```python
from django_stacktrace.event_store import store_crash_event

try:
    1 / 0
except Exception as exc:
    store_crash_event(exc=exc)
```

## Settings

All settings live under a single `STACKTRACE` dictionary. Each key is optional.

```python
STACKTRACE = {
    "STACKTRACE_ENABLED": True,
    "STACKTRACE_SAMPLE_RATE": 1.0,
    "STACKTRACE_RATE_LIMIT": 0,
    "STACKTRACE_CAPTURE_HEADERS": True,
    "STACKTRACE_CAPTURE_BODY": False,
    "STACKTRACE_MAX_PAYLOAD_BYTES": 64 * 1024,
    "STACKTRACE_REDACT_FIELDS": ["password", "token"],
    "STACKTRACE_REDACT_HEADERS": ["authorization", "cookie"],
    "STACKTRACE_USER_FIELD": "username",
}
```

Available keys:

- `STACKTRACE_ENABLED` (default `True`)
- `STACKTRACE_SAMPLE_RATE` (default `1.0`, 0-1 sampling probability)
- `STACKTRACE_RATE_LIMIT` (default `0`, per-minute cap; `0` disables)
- `STACKTRACE_CAPTURE_HEADERS` (default `True`)
- `STACKTRACE_CAPTURE_BODY` (default `False`)
- `STACKTRACE_MAX_PAYLOAD_BYTES` (default `65536`)
- `STACKTRACE_REDACT_FIELDS` (request keys to mask)
- `STACKTRACE_REDACT_HEADERS` (header keys to mask)
- `STACKTRACE_USER_FIELD` (user attribute for display name)

## Settings reference

`STACKTRACE_ENABLED`

- Type: `bool`
- Purpose: Enable or disable crash capturing entirely.
- Example: `"STACKTRACE_ENABLED": False`

`STACKTRACE_SAMPLE_RATE`

- Type: `float` between `0.0` and `1.0`
- Purpose: Probabilistic sampling for high-volume apps.
- Example: `"STACKTRACE_SAMPLE_RATE": 0.1`

`STACKTRACE_RATE_LIMIT`

- Type: `int`
- Purpose: Per-minute cap; `0` disables rate limiting.
- Example: `"STACKTRACE_RATE_LIMIT": 120`

`STACKTRACE_CAPTURE_HEADERS`

- Type: `bool`
- Purpose: Include request headers in the captured event.
- Example: `"STACKTRACE_CAPTURE_HEADERS": True`

`STACKTRACE_CAPTURE_BODY`

- Type: `bool`
- Purpose: Include request body in the captured event.
- Example: `"STACKTRACE_CAPTURE_BODY": False`

`STACKTRACE_MAX_PAYLOAD_BYTES`

- Type: `int`
- Purpose: Max bytes kept from request body.
- Example: `"STACKTRACE_MAX_PAYLOAD_BYTES": 65536`

`STACKTRACE_REDACT_FIELDS`

- Type: `list[str]` or `set[str]`
- Purpose: Request data keys to mask before storage.
- Example: `"STACKTRACE_REDACT_FIELDS": ["password", "token"]`

`STACKTRACE_REDACT_HEADERS`

- Type: `list[str]` or `set[str]`
- Purpose: Header keys to mask before storage.
- Example: `"STACKTRACE_REDACT_HEADERS": ["authorization", "cookie"]`

`STACKTRACE_USER_FIELD`

- Type: `str`
- Purpose: User attribute used for display name in the event.
- Example: `"STACKTRACE_USER_FIELD": "username"`

## Data model

Events are stored in `django_stacktrace.CrashEvent` with indexed fields like level,
logger, error type, request path, user identifier, and traceback hash, plus a
JSON payload for full context.

## Backlog

- Async storage path (Celery/queue support)
- Logging integration for `logging` exceptions
- Rate-limit options (per-user/IP limits, key prefix)
- Body size controls (per-content-type limits, truncation)
- Filtering hooks (ignore exceptions or URLs)
- Admin UI improvements (grouping, search, trends)
- Export and retention tools (cleanup, CSV export)