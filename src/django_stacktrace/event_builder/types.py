"""
Type definitions for crash event data structures.
Follows Sentry-compatible data model.
"""

from datetime import datetime
from typing import Any, Dict, NotRequired, Optional, TypedDict, Union


class StackFrameData(TypedDict, total=False):
    filename: str
    abs_path: str
    function: str
    lineno: int
    context_line: Optional[str]
    in_app: bool


class ExceptionStacktraceData(TypedDict):
    frames: list[StackFrameData]


class ExceptionValueData(TypedDict):
    type: str
    value: str
    module: str
    stacktrace: ExceptionStacktraceData


class ExceptionData(TypedDict):
    values: list[ExceptionValueData]


class RequestEnvData(TypedDict):
    SERVER_NAME: Optional[str]
    SERVER_PORT: Optional[str]


class RequestData(TypedDict, total=False):
    url: str
    method: str
    query_string: Dict[str, Any]
    data: Union[Dict[str, Any], str, None]
    headers: Dict[str, Any]
    env: RequestEnvData
    data_compressed: bool
    data_truncated: bool


class UserData(TypedDict):
    id: Optional[str]
    username_field_key: NotRequired[str]
    username_field_value: NotRequired[Optional[str]]
    ip_address: str


class RuntimeContextData(TypedDict):
    name: str
    version: str
    build: str


class OSContextData(TypedDict):
    name: str
    kernel_version: str
    version: str


class DjangoContextData(TypedDict):
    app_name: str
    app_version: str
    settings_module: str


class DBContextData(TypedDict, total=False):
    vendor: str
    alias: str
    name: str
    engine: str


class TracebackContextData(TypedDict):
    raw: str


class ContextsData(TypedDict, total=False):
    runtime: RuntimeContextData
    os: OSContextData
    django: DjangoContextData
    db: DBContextData
    traceback: TracebackContextData


class CrashEventData(TypedDict):
    event_id: str
    timestamp: datetime
    level: str
    logger: str
    platform: str
    server_name: str
    contexts: ContextsData
    exception: NotRequired[ExceptionData]
    request: NotRequired[RequestData]
    user: NotRequired[UserData]
    extra: NotRequired[Dict[str, Any]]
    culprit: NotRequired[str]
    main_error_type: NotRequired[str]
    main_error_message: NotRequired[str]


__all__ = [
    "StackFrameData",
    "ExceptionStacktraceData",
    "ExceptionValueData",
    "ExceptionData",
    "RequestEnvData",
    "RequestData",
    "UserData",
    "RuntimeContextData",
    "OSContextData",
    "DjangoContextData",
    "DBContextData",
    "TracebackContextData",
    "ContextsData",
    "CrashEventData",
]
