import sys

from django_stacktrace.event_store import store_crash_event


class StacktraceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if getattr(request, "_stacktrace_captured", False):
            return None
        request._stacktrace_captured = True
        store_crash_event(
            request=request,
            exc=exception,
            exc_info=sys.exc_info(),
            level="ERROR",
            logger_name="django.request",
        )
        return None
