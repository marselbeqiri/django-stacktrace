import logging
import threading
from typing import Any, Dict, Optional, Tuple

from django.db.models import F

from django_crashlog.event_builder import build_crash_event
from django_crashlog.event_builder.types import CrashEventData
from django_crashlog.models import CrashEvent
from django_crashlog.settings import api_settings

from django_crashlog.event_store.model_data import build_crash_event_model_data
from django_crashlog.event_store.sampling import (
    is_within_rate_limit,
    should_sample_event,
)

CRASHLOG_ENABLED = api_settings.CRASHLOG_ENABLED
CRASHLOG_ASYNC_HANDLER = None

_thread_state = threading.local()

logger = logging.getLogger("django_crashlog.event_store")


def _persist_crash_event(model_data: Dict[str, Any]) -> Optional[CrashEvent]:
    """
    Persists crash event data into the database.
    If traceback_hash already exists, increments occurrence_count.
    Otherwise creates a new record.
    """
    traceback_hash = model_data.get("traceback_hash")
    if not traceback_hash:
        logger.warning("Cannot store event without traceback_hash")
        return None
    try:
        updated = CrashEvent.objects.filter(traceback_hash=traceback_hash).update(
            occurrence_count=F("occurrence_count") + 1,
            context=model_data["context"],
        )

        if updated:
            return CrashEvent.objects.get(traceback_hash=traceback_hash)

        return CrashEvent.objects.create(**model_data)
    except Exception as exc:
        logger.error("Failed to store crash event: %s", exc, exc_info=True)
        return None


def store_crash_event(
    *,
    request: Any = None,
    exc: Optional[BaseException] = None,
    exc_info: Optional[Tuple[Any, Any, Any]] = None,
    level: str = "error",
    logger_name: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[CrashEvent]:
    """
    Public API to capture and store an exception.
    """
    if not CRASHLOG_ENABLED:
        return None

    if getattr(_thread_state, "in_capture", False):
        return None

    if not should_sample_event() or not is_within_rate_limit():
        return None

    _thread_state.in_capture = True
    try:
        event: CrashEventData = build_crash_event(
            request=request,
            exc=exc,
            exc_info=exc_info,
            level=level,
            logger_name=logger_name,
            extra=extra,
        )
        model_data = build_crash_event_model_data(event)
        return _persist_crash_event(model_data)
    except Exception:
        logger.error("Critical error while storing crash event", exc_info=True)
        return None
    finally:
        _thread_state.in_capture = False
