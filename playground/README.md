# Playground

Run the demo project:

- `python manage.py migrate`
- `python manage.py runserver`

Trigger a test error:

- `http://localhost:8000/crashlog/crashlog/ValueError/`
- `http://localhost:8000/crashlog/crashlog/KeyError/`

Check captured events in the Django admin under `Crash events`.