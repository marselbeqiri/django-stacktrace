from django.conf import settings
from django.core.signals import setting_changed

DEFAULTS = {
    "CRASHLOG_ENABLED": True,
    "CRASHLOG_SAMPLE_RATE": 1.0,
    "CRASHLOG_RATE_LIMIT": 0,
    "CRASHLOG_CAPTURE_HEADERS": True,
    "CRASHLOG_CAPTURE_BODY": False,
    "CRASHLOG_MAX_PAYLOAD_BYTES": 64 * 1024,
    # Builder options
    "CRASHLOG_REDACT_FIELDS": {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "authorization",
        "cookie",
        "session",
    },
    "CRASHLOG_REDACT_HEADERS": {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-csrf-token",
    },
    "CRASHLOG_USER_FIELD": "username",
}
USER_SETTINGS = getattr(settings, "CRASHLOG", None)


class APISettings:

    def __init__(self, user_settings=None, defaults=None):
        self.user_settings = user_settings or DEFAULTS
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)

        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


api_settings = APISettings(
    user_settings=USER_SETTINGS,
    defaults=DEFAULTS,
)


def reload_api_settings(*args, **kwargs) -> None:
    setting = kwargs["setting"]
    if setting == "CRASHLOG":
        api_settings.reload()


setting_changed.connect(reload_api_settings)
