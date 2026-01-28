import json
import sys

from django.test import RequestFactory, SimpleTestCase

from django_stacktrace.event_builder.builder import build_crash_event
from django_stacktrace.event_builder.exception import collect_exception
from django_stacktrace.event_builder.request import (
    collect_request,
    extract_request_body,
)
from django_stacktrace.event_builder.user import collect_user


class EventBuilderTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_build_crash_event_includes_exception_context_and_request_culprit(self):
        request = self.factory.get("/boom/")

        try:
            raise ValueError("boom")
        except ValueError as exc:
            event = build_crash_event(request=request, exc=exc, exc_info=sys.exc_info())

        self.assertTrue(event["exception"]["values"])
        self.assertEqual(event["main_error_type"], "ValueError")
        self.assertTrue(event["request"]["url"].endswith("/boom/"))
        self.assertEqual(event["culprit"], event["request"]["url"])
        self.assertIn("contexts", event)

    def test_collect_exception_includes_stacktrace_frames(self):
        try:
            raise RuntimeError("bad")
        except RuntimeError as exc:
            data = collect_exception(exc, sys.exc_info())

        frames = data["exception"]["values"][0]["stacktrace"]["frames"]
        self.assertTrue(frames)

    def test_collect_request_redacts_query_and_headers(self):
        request = self.factory.get(
            "/search/?password=secret&ok=1",
            HTTP_AUTHORIZATION="Bearer secret",
        )

        result = collect_request(
            request,
            redact_keys={"password"},
            redact_headers={"authorization"},
            capture_body=False,
            capture_headers=True,
            max_body_bytes=1024,
        )

        self.assertEqual(result["query_string"]["password"], "*****")
        self.assertEqual(result["query_string"]["ok"], "1")
        self.assertEqual(result["headers"]["Authorization"], "*****")

    def test_extract_request_body_truncates_large_payload(self):
        payload = {"payload": "x" * 1000}
        request = self.factory.post(
            "/submit/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        body_data, metadata = extract_request_body(
            request,
            redact_keys=set(),
            max_body_bytes=10,
        )

        self.assertTrue(metadata.get("data_truncated"))
        self.assertIsInstance(body_data, str)

    def test_collect_user_returns_anonymous_with_ip(self):
        request = self.factory.get("/profile/")
        request.META["REMOTE_ADDR"] = "10.0.0.5"

        user_data = collect_user(request, "username")

        self.assertIsNone(user_data["id"])
        self.assertEqual(user_data["ip_address"], "10.0.0.5")
