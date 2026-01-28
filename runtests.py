import os


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_stacktrace.tests.settings")

    import django
    from django.conf import settings
    from django.test.utils import get_runner

    django.setup()
    test_runner_class = get_runner(settings)
    test_runner = test_runner_class(verbosity=1, interactive=True)
    failures = test_runner.run_tests(["django_stacktrace"])
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
