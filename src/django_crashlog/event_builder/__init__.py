"""
Crash event builder module.

The primary API is `build_crash_event()` which builds a Sentry-compatible
crash event from an exception and optional request.
"""

from .builder import build_crash_event
from .types import CrashEventData


def get_event_builder():
    """
    Backward compatibility shim.

    Deprecated: Use `build_crash_event()` directly instead.

    Returns:
        A wrapper object with a `build_event()` method that delegates
        to `build_crash_event()`.
    """

    class _CompatBuilder:
        def build_event(self, **kwargs):
            return build_crash_event(**kwargs)

    return _CompatBuilder()


__all__ = ["build_crash_event", "CrashEventData", "get_event_builder"]
