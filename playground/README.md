# Playground

Run the demo project:

- `python manage.py migrate`
- `python manage.py runserver`

Trigger a test error:

- `http://localhost:8000/stacktrace/stacktrace/ValueError/`
- `http://localhost:8000/stacktrace/stacktrace/KeyError/`

Check captured events in the Django admin under `Crash events`.