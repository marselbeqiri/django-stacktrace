from django.apps import AppConfig


class StacktraceConfig(AppConfig):
    name = "django_stacktrace"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import django_stacktrace.signals  # noqa
