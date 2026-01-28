## Running tests

Two supported ways:

```bash
uv run python runtests.py
```

```bash
DJANGO_SETTINGS_MODULE=django_stacktrace.tests.settings uv run python -m django test django_stacktrace
```
