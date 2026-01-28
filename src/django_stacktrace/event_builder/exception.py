"""
Exception processing utilities.
"""

import logging
import sys
import traceback
from typing import Any, Dict, Optional, Tuple

from .types import ExceptionData, ExceptionValueData, StackFrameData

logger = logging.getLogger("django_stacktrace.event_builder")


def format_traceback(
    exc: Optional[BaseException],
    exc_info: Optional[Tuple[Any, Any, Any]],
) -> str:
    """
    Format exception as a traceback string.

    Args:
        exc: Exception instance
        exc_info: Exception info tuple (type, value, traceback)

    Returns:
        Formatted traceback string
    """
    tb = None
    if exc_info and exc_info[2]:
        tb = exc_info[2]
    elif exc:
        tb = getattr(exc, "__traceback__", None)

    try:
        if exc_info and exc_info[0]:
            return "".join(traceback.format_exception(*exc_info))
        if exc:
            return "".join(traceback.format_exception(type(exc), exc, tb))
    except Exception as e:
        logger.warning("Failed to format traceback: %s", e)
        return "Could not format traceback."

    return ""


def process_exception(
    exc: Optional[BaseException],
    exc_info: Optional[Tuple[Any, Any, Any]],
) -> ExceptionData:
    """
    Process exception into Sentry-compatible exception interface.

    Args:
        exc: Exception instance
        exc_info: Exception info tuple (type, value, traceback)

    Returns:
        ExceptionData with structure: {"values": [{"type": ..., "value": ..., "stacktrace": ...}]}
    """
    if not exc_info:
        exc_info = sys.exc_info()
    if not exc and exc_info:
        exc = exc_info[1]

    if not exc:
        return {"values": []}

    tb = (
        exc_info[2] if exc_info and exc_info[2] else getattr(exc, "__traceback__", None)
    )

    frames: list[StackFrameData] = []
    if tb:
        for frame in traceback.extract_tb(tb):
            frames.append(
                StackFrameData(
                    filename=str(frame.filename),
                    abs_path=str(frame.filename),
                    function=str(frame.name),
                    lineno=int(frame.lineno) if frame.lineno is not None else 0,
                    context_line=str(frame.line) if frame.line else None,
                )
            )

    module_name = getattr(type(exc), "__module__", "builtins")

    exception_value: ExceptionValueData = {
        "type": type(exc).__name__,
        "value": str(exc),
        "module": module_name,
        "stacktrace": {"frames": frames},
    }

    return {"values": [exception_value]}


def collect_exception(
    exc: Optional[BaseException],
    exc_info: Optional[Tuple[Any, Any, Any]],
) -> Dict[str, Any]:
    """
    Collect exception data including main error type, message, and culprit.

    Args:
        exc: Exception instance
        exc_info: Exception info tuple (type, value, traceback)

    Returns:
        Dictionary with keys:
        - exception: ExceptionData structure
        - main_error_type: String name of exception type
        - main_error_message: String exception message
        - culprit: String identifying the culprit (top frame function/filename)
    """
    exception_data = process_exception(exc, exc_info)

    if not exception_data["values"]:
        return {}

    result: Dict[str, Any] = {"exception": exception_data}

    main_exception = exception_data["values"][0]
    result["main_error_type"] = main_exception.get("type", "UnknownError")
    result["main_error_message"] = main_exception.get("value", "")

    frames = main_exception.get("stacktrace", {}).get("frames", [])
    if frames:
        top_frame = frames[-1]
        result["culprit"] = top_frame.get("function") or top_frame.get("filename")

    return result


__all__ = ["collect_exception", "format_traceback", "process_exception"]
