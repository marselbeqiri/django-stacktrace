import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest

from django_stacktrace.event_builder.types import CrashEventData

logger = logging.getLogger("django_stacktrace.event_store")


class StacktraceEncoder(DjangoJSONEncoder):
    """
    Ensures absolute safety when serializing the context to JSON.
    """

    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, HttpRequest):
            return None
        if isinstance(obj, set):
            return list(obj)
        try:
            return super().default(obj)
        except Exception:
            return str(obj)


def build_traceback_hash(
    exception_data: Dict[str, Any],
    error_type: str = "",
    error_message: str = "",
    request_method: str = "",
    request_path: str = "",
    request_data_keys: Optional[list] = None,
) -> str:
    """
    Generates a hash based on exception type, request context, and stacktrace frames.

    Hash components (in order):
    1. Exception type (e.g., "ValueError", "KeyError")
    2. Request method if present (e.g., "POST", "GET")
    3. Request path if present (e.g., "/api/users")
    4. Payload structure - sorted keys only (e.g., "age,name,user")
    5. Stack frames (module, filename, function - ignoring line numbers)
    6. Fallback to error message if no frames
    """
    try:
        hash_parts = []

        if error_type:
            hash_parts.append(f"type:{error_type}")

        values = exception_data.get("values", [])

        if values:
            main_exc = values[0]
            exc_type = main_exc.get("type", "")
            exc_module = main_exc.get("module", "")

            if exc_type and not error_type:
                hash_parts.append(
                    f"type:{exc_module}.{exc_type}"
                    if exc_module
                    else f"type:{exc_type}"
                )

        if request_method:
            hash_parts.append(f"method:{request_method.upper()}")

        if request_path:
            hash_parts.append(f"path:{request_path}")

        if request_data_keys:
            keys_str = ",".join(sorted(request_data_keys))
            hash_parts.append(f"keys:{keys_str}")

        if values:
            main_exc = values[0]
            stacktrace = main_exc.get("stacktrace", {})
            frames = stacktrace.get("frames", [])

            for frame in frames:
                mod = frame.get("module", "")
                func = frame.get("function", "")
                fname = frame.get("filename", "")
                hash_parts.append(f"frame:{mod}|{fname}|{func}")

        if not any(p.startswith("frame:") for p in hash_parts):
            if error_message:
                normalized_msg = error_message[:200].strip()
                hash_parts.append(f"msg:{normalized_msg}")

        if not hash_parts:
            return hashlib.sha256(
                str(datetime.now(timezone.utc).timestamp()).encode()
            ).hexdigest()

        hash_content = ";".join(hash_parts)
        return hashlib.sha256(hash_content.encode("utf-8")).hexdigest()
    except Exception as exc:
        logger.warning("Failed to calculate traceback hash: %s", exc)
        return hashlib.sha256(
            str(datetime.now(timezone.utc).timestamp()).encode()
        ).hexdigest()


def build_crash_event_model_data(event: CrashEventData) -> Dict[str, Any]:
    """
    Maps a crash event payload to CrashEvent model field values.
    """
    exception_info = event.get("exception", {})
    error_type = event.get("main_error_type") or "UnknownError"
    error_message = event.get("main_error_message") or ""

    request_info = event.get("request", {})

    user_info = event.get("user", {})
    user_ident = (
        user_info.get("id")
        or user_info.get("username_field_value")
        or user_info.get("ip_address")
        or "Anonymous"
    )

    request_data = request_info.get("data")
    request_data_keys = []
    if isinstance(request_data, dict):
        request_data_keys = sorted(request_data.keys())

    tb_hash = build_traceback_hash(
        exception_data=exception_info,
        error_type=error_type,
        error_message=error_message,
        request_method=request_info.get("method", ""),
        request_path=request_info.get("url", ""),
        request_data_keys=request_data_keys,
    )

    context_data = event.copy()
    for key in (
        "event_id",
        "level",
        "logger",
        "server_name",
        "culprit",
        "main_error_type",
        "main_error_message",
    ):
        context_data.pop(key, None)

    json_parsable_ctx = json.loads(json.dumps(context_data, cls=StacktraceEncoder))

    return {
        "traceback_hash": tb_hash,
        "event_id": event.get("event_id"),
        "level": event.get("level", "error"),
        "logger": event.get("logger", ""),
        "server_name": event.get("server_name", ""),
        "error_type": error_type[:255],
        "message": error_message,
        "culprit": event.get("culprit", "")[:512],
        "request_path": request_info.get("url", "")[:2048],
        "request_method": request_info.get("method", "")[:16],
        "user_identifier": str(user_ident)[:255],
        "remote_addr": user_info.get("ip_address") or "",
        "context": json_parsable_ctx,
    }
