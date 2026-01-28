import logging
import os
import platform

import django
from django.db import connection

from .types import (
    ContextsData,
    DBContextData,
    DjangoContextData,
    OSContextData,
    RuntimeContextData,
    TracebackContextData,
)

logger = logging.getLogger("django_stacktrace.event_builder")


def collect_contexts(raw_traceback: str = "") -> ContextsData:
    """
    Collect runtime, OS, Django, and database context.

    Args:
        raw_traceback: Raw traceback string to include in contexts

    Returns:
        ContextsData with runtime, os, django, db, and optionally traceback keys
    """
    impl = platform.python_implementation()
    runtime: RuntimeContextData = {
        "name": "CPython" if impl == "CPython" else impl,
        "version": platform.python_version(),
        "build": platform.python_build()[0],
    }

    os_ctx: OSContextData = {
        "name": platform.system(),
        "kernel_version": platform.release(),
        "version": platform.version(),
    }

    django_ctx: DjangoContextData = {
        "app_name": "Django",
        "app_version": django.get_version(),
        "settings_module": os.environ.get("DJANGO_SETTINGS_MODULE", "unknown"),
    }

    try:
        db_ctx: DBContextData = {
            "vendor": connection.vendor,
            "alias": connection.alias,
            "name": connection.settings_dict.get("NAME"),
            "engine": connection.settings_dict.get("ENGINE"),
        }
    except Exception as e:
        logger.warning("Failed to extract database context: %s", e)
        db_ctx = {}

    contexts: ContextsData = {
        "runtime": runtime,
        "os": os_ctx,
        "django": django_ctx,
        "db": db_ctx,
    }

    if raw_traceback:
        contexts["traceback"] = TracebackContextData(raw=raw_traceback)

    return contexts
