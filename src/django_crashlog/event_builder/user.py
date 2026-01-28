from django.http import HttpRequest

from .types import UserData


def collect_user(request: HttpRequest, user_field: str) -> UserData:
    """
    Extract user information from Django HttpRequest.

    Args:
        request: Django HttpRequest
        user_field: Name of the user attribute to use for display name

    Returns:
        UserData dictionary with user ID, display name, and IP address
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")
    ip_address = str(ip_address) if ip_address else ""

    user = getattr(request, "user", None)

    if not user:
        return {"id": None, "ip_address": ip_address}

    is_authenticated = getattr(user, "is_authenticated", False)
    if callable(is_authenticated):
        is_authenticated = is_authenticated()

    if not is_authenticated:
        return {
            "id": None,
            "username_field_key": user_field,
            "username_field_value": "Anonymous",
            "ip_address": ip_address,
        }

    user_id = str(getattr(user, "pk", getattr(user, "id", "unknown")))
    user_display = str(getattr(user, user_field, user))

    return {
        "id": user_id,
        "username_field_key": user_field,
        "username_field_value": user_display,
        "ip_address": ip_address,
    }
