from django.apps import AppConfig


class CrashlogConfig(AppConfig):
    name = "django_crashlog"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import django_crashlog.signals  # noqa
