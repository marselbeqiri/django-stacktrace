"""
Function-oriented crash event builder.

This module provides a single orchestrator function `build_crash_event()`
and delegates all data collection to focused helper modules.
"""

import socket
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from django.http import HttpRequest

from django_crashlog.settings import api_settings
from .contexts import collect_contexts
from .exception import collect_exception, format_traceback
from .request import collect_request
from .serialization import SerializationHelper
from .types import CrashEventData
from .user import collect_user


def build_crash_event(
    *,
    request: Optional[HttpRequest] = None,
    exc: Optional[BaseException] = None,
    exc_info: Optional[Tuple[Any, Any, Any]] = None,
    level: str = "error",
    logger_name: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    redact_keys: Optional[set[str]] = None,
    redact_headers: Optional[set[str]] = None,
    capture_body: Optional[bool] = None,
    capture_headers: Optional[bool] = None,
    max_body_bytes: Optional[int] = None,
    user_field: Optional[str] = None,
) -> CrashEventData:
    """
    Build a complete crash event from an exception and optional request.

    This is the single orchestrator function for building Sentry-compatible
    crash events. All configuration has sensible defaults from settings.

    Args:
        request: Optional Django HttpRequest
        exc: Optional exception instance
        exc_info: Optional exception info tuple (type, value, traceback)
        level: Log level (default: "error")
        logger_name: Name of the logger
        extra: Additional context data
        redact_keys: Keys to redact from request data (default from settings)
        redact_headers: Headers to redact (default from settings)
        capture_body: Whether to capture request body (default from settings)
        capture_headers: Whether to capture headers (default from settings)
        max_body_bytes: Maximum body size (default from settings)
        user_field: User field for display name (default from settings)

    Returns:
        CrashEventData dictionary ready for storage
    """
    if redact_keys is None:
        redact_keys = api_settings.CRASHLOG_REDACT_FIELDS
    if redact_headers is None:
        redact_headers = api_settings.CRASHLOG_REDACT_HEADERS
    if capture_body is None:
        capture_body = api_settings.CRASHLOG_CAPTURE_BODY
    if capture_headers is None:
        capture_headers = api_settings.CRASHLOG_CAPTURE_HEADERS
    if max_body_bytes is None:
        max_body_bytes = api_settings.CRASHLOG_MAX_PAYLOAD_BYTES
    if user_field is None:
        user_field = api_settings.CRASHLOG_USER_FIELD

    raw_traceback = format_traceback(exc, exc_info)

    event: CrashEventData = {
        "event_id": uuid.uuid4().hex,
        "timestamp": datetime.now(timezone.utc),
        "level": level.lower(),
        "logger": str(logger_name) if logger_name else "root",
        "platform": "python",
        "server_name": socket.gethostname(),
        "contexts": collect_contexts(raw_traceback),
    }

    exception_result = collect_exception(exc, exc_info)
    if exception_result:
        event.update(exception_result)

    if request:
        event["request"] = collect_request(
            request,
            redact_keys=redact_keys,
            redact_headers=redact_headers,
            capture_body=capture_body,
            capture_headers=capture_headers,
            max_body_bytes=max_body_bytes,
        )
        event["user"] = collect_user(request, user_field)

        if event["request"].get("url"):
            event["culprit"] = event["request"]["url"]

    if extra:
        clean_extra = SerializationHelper.to_encodable(extra)
        if clean_extra:
            event["extra"] = clean_extra

    return event
