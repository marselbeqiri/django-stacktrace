import base64
import gzip
import json
import logging
from typing import Any, Dict, Tuple

from django.http import HttpRequest

from .serialization import SerializationHelper
from .types import RequestData, RequestEnvData

logger = logging.getLogger("django_stacktrace.event_builder")


def redact_dict(data: Dict[str, Any], keys: set[str]) -> Dict[str, Any]:
    """
    Recursively redact sensitive keys in a dictionary.

    Args:
        data: Dictionary to redact
        keys: Set of lowercase key names to redact

    Returns:
        New dictionary with sensitive values replaced by "*****"
    """
    if not data:
        return {}

    normalized_keys = {k.lower() for k in keys}
    redacted: Dict[str, Any] = {}

    for k, v in data.items():
        if str(k).lower() in normalized_keys:
            redacted[k] = "*****"
        elif isinstance(v, dict):
            redacted[k] = redact_dict(v, normalized_keys)
        else:
            redacted[k] = v

    return redacted


def extract_request_body(
    request: HttpRequest,
    *,
    redact_keys: set[str],
    max_body_bytes: int,
) -> Tuple[Any, Dict[str, bool]]:
    """
    Extract and process request body for POST/PUT/PATCH methods.

    Applies compression or truncation if body exceeds max_body_bytes.

    Args:
        request: Django HttpRequest
        redact_keys: Keys to redact from body data
        max_body_bytes: Maximum body size before compression/truncation

    Returns:
        Tuple of (body_data, metadata) where metadata contains:
        - data_compressed: True if body was gzip compressed
        - data_truncated: True if body was truncated
    """
    metadata: Dict[str, bool] = {}

    if request.POST:
        data = SerializationHelper.to_encodable(dict(request.POST.items()))
        body_data = redact_dict(data, redact_keys)
    else:
        try:
            raw_body = request.body
            if not raw_body:
                return None, metadata
            try:
                json_body = json.loads(raw_body)
                body_data = redact_dict(json_body, redact_keys)
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse request body as JSON: %s", e)
                decoded = raw_body.decode("utf-8", errors="replace")
                body_data = {"_raw": decoded}
        except Exception as e:
            logger.warning("Failed to read request body: %s", e)
            return {"_error": "Body unavailable"}, metadata

    serialized = json.dumps(body_data, default=str)
    body_size = len(serialized.encode("utf-8"))

    if body_size <= max_body_bytes:
        return body_data, metadata

    compressed_bytes = gzip.compress(serialized.encode("utf-8"))
    compressed = base64.b64encode(compressed_bytes).decode("ascii")

    if len(compressed) <= max_body_bytes:
        metadata["data_compressed"] = True
        return compressed, metadata

    marker = "... [truncated]"
    max_content = max_body_bytes - len(marker)
    if max_content <= 0:
        truncated = marker
    else:
        truncated = serialized[:max_content] + marker

    metadata["data_truncated"] = True
    return truncated, metadata


def collect_request(
    request: HttpRequest,
    *,
    redact_keys: set[str],
    redact_headers: set[str],
    capture_body: bool,
    capture_headers: bool,
    max_body_bytes: int,
) -> RequestData:
    """
    Extract request data from Django HttpRequest.

    Args:
        request: Django HttpRequest
        redact_keys: Keys to redact from query string and body
        redact_headers: Header names to redact
        capture_body: Whether to capture request body
        capture_headers: Whether to capture request headers
        max_body_bytes: Maximum body size before compression/truncation

    Returns:
        RequestData dictionary with URL, method, headers, body, etc.
    """
    try:
        url = request.build_absolute_uri()
    except Exception as e:
        logger.warning("Failed to build absolute URI: %s", e)
        url = request.path

    method = request.method or ""

    query_data = SerializationHelper.to_encodable(dict(request.GET.items()))
    query_string = redact_dict(query_data, redact_keys)

    if capture_headers:
        headers_data = SerializationHelper.to_encodable(dict(request.headers))
        headers = redact_dict(headers_data, redact_headers)
    else:
        headers = {}

    env: RequestEnvData = {
        "SERVER_NAME": request.META.get("SERVER_NAME"),
        "SERVER_PORT": request.META.get("SERVER_PORT"),
    }

    body_data = None
    body_metadata: Dict[str, bool] = {}

    if capture_body and method.upper() in ("POST", "PUT", "PATCH"):
        body_data, body_metadata = extract_request_body(
            request,
            redact_keys=redact_keys,
            max_body_bytes=max_body_bytes,
        )

    result: RequestData = {
        "url": url,
        "method": method,
        "query_string": query_string,
        "headers": headers,
        "env": env,
        "data": body_data,
    }

    if body_metadata.get("data_compressed"):
        result["data_compressed"] = True
    if body_metadata.get("data_truncated"):
        result["data_truncated"] = True

    return result
