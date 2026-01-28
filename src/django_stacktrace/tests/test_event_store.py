from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from django_stacktrace.event_store.store import store_crash_event


class EventStoreTests(SimpleTestCase):
    def test_store_crash_event_disabled_returns_none(self):
        with (
            patch("django_stacktrace.event_store.store.STACKTRACE_ENABLED", False),
            patch(
                "django_stacktrace.event_store.store.build_crash_event"
            ) as build_crash_event,
        ):
            result = store_crash_event()

        self.assertIsNone(result)
        build_crash_event.assert_not_called()

    def test_store_crash_event_skips_when_sampling_or_rate_limit_blocks(self):
        with (
            patch(
                "django_stacktrace.event_store.store.should_sample_event",
                return_value=False,
            ),
            patch(
                "django_stacktrace.event_store.store.is_within_rate_limit",
                return_value=True,
            ),
        ):
            result = store_crash_event()
        self.assertIsNone(result)

        with (
            patch(
                "django_stacktrace.event_store.store.should_sample_event",
                return_value=True,
            ),
            patch(
                "django_stacktrace.event_store.store.is_within_rate_limit",
                return_value=False,
            ),
        ):
            result = store_crash_event()
        self.assertIsNone(result)

    def test_store_crash_event_creates_new_record_when_no_existing_hash(self):
        model_data = {"traceback_hash": "hash-1", "context": {"k": "v"}}
        created = Mock(name="created_event")
        objects = Mock()
        objects.filter.return_value.update.return_value = 0
        objects.create.return_value = created

        with (
            patch(
                "django_stacktrace.event_store.store.build_crash_event",
                return_value={"event": "data"},
            ),
            patch(
                "django_stacktrace.event_store.store.build_crash_event_model_data",
                return_value=model_data,
            ),
            patch("django_stacktrace.event_store.store.CrashEvent.objects", objects),
        ):
            result = store_crash_event()

        self.assertIs(result, created)
        objects.create.assert_called_once_with(**model_data)

    def test_store_crash_event_returns_existing_record_when_updated(self):
        model_data = {"traceback_hash": "hash-2", "context": {"k": "v"}}
        existing = Mock(name="existing_event")
        objects = Mock()
        objects.filter.return_value.update.return_value = 1
        objects.get.return_value = existing

        with (
            patch(
                "django_stacktrace.event_store.store.build_crash_event",
                return_value={"event": "data"},
            ),
            patch(
                "django_stacktrace.event_store.store.build_crash_event_model_data",
                return_value=model_data,
            ),
            patch("django_stacktrace.event_store.store.CrashEvent.objects", objects),
        ):
            result = store_crash_event()

        self.assertIs(result, existing)
        objects.get.assert_called_once_with(traceback_hash="hash-2")
