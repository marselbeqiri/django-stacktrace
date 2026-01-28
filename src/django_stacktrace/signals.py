from django.core.signals import got_request_exception
from django.dispatch import receiver
import sys

from django_stacktrace.event_store import store_crash_event


@receiver(got_request_exception)
def handle_exception(sender, request, **kwargs):
    if getattr(request, "_stacktrace_captured", False):
        return

    request._stacktrace_captured = True
    exc = kwargs.get("exception") or sys.exc_info()[1]
    store_crash_event(
        request=request,
        exc=exc,
        exc_info=sys.exc_info(),
        level="ERROR",
        logger_name="django.request",
        extra={"signal": "got_request_exception"},
    )
