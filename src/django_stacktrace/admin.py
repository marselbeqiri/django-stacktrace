import json
from datetime import datetime, timezone

from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince

from .models import CrashEvent


def format_count(count: int) -> str:
    """Format large numbers with k/M suffix."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return str(count)


@admin.register(CrashEvent)
class CrashEventAdmin(admin.ModelAdmin):
    list_display = (
        "error_summary",
        "level_badge",
        "events_count",
        "time_info",
        "logger_display",
        "request_info",
    )

    list_filter = (
        "level",
        "error_type",
        "server_name",
        "request_method",
    )

    search_fields = (
        "error_type",
        "message",
        "traceback_hash",
        "request_path",
        "user_identifier",
        "culprit",
    )

    date_hierarchy = "last_seen_at"
    list_per_page = 25
    ordering = ["-last_seen_at"]

    readonly_fields = (
        "event_id",
        "created_at",
        "last_seen_at",
        "occurrence_count",
        "level",
        "logger",
        "error_type",
        "message",
        "culprit",
        "request_path",
        "request_method",
        "user_identifier",
        "remote_addr",
        "server_name",
        "traceback_hash",
        "tags_display",
        "exception_display",
        "request_display",
        "user_display",
        "context_display",
    )

    fieldsets = (
        (
            "Error Overview",
            {
                "fields": (
                    "event_id",
                    "level",
                    "error_type",
                    "message",
                    "culprit",
                    "logger",
                    "traceback_hash",
                )
            },
        ),
        (
            "Occurrence",
            {
                "fields": (
                    "occurrence_count",
                    "created_at",
                    "last_seen_at",
                )
            },
        ),
        (
            "Tags",
            {
                "fields": ("tags_display",),
            },
        ),
        (
            "Exception",
            {
                "fields": ("exception_display",),
            },
        ),
        (
            "Request",
            {
                "fields": ("request_display",),
            },
        ),
        (
            "User",
            {
                "fields": ("user_display",),
            },
        ),
        (
            "Full Context (JSON)",
            {
                "fields": ("context_display",),
                "classes": ("collapse",),
            },
        ),
    )

    # -------------------- List Display Methods --------------------

    @admin.display(description="Issue")
    def error_summary(self, obj):
        """Error summary with type, culprit, message, and ID."""
        error_type = obj.error_type or "Exception"
        culprit = obj.culprit or ""
        message = obj.message or ""

        if len(message) > 80:
            message = message[:80] + "..."

        if len(culprit) > 50:
            culprit = "..." + culprit[-47:]

        short_id = str(obj.event_id)[:8].upper() if obj.event_id else ""

        return format_html(
            '<div class="stacktrace-error-type"><a href="{}">{}</a></div>'
            '<div class="stacktrace-culprit">{}</div>'
            '<div class="stacktrace-message">{}</div>'
            '<span class="stacktrace-event-id">{}</span>',
            f"{obj.pk}/change/",
            error_type,
            culprit,
            message,
            short_id,
        )

    @admin.display(description="Level")
    def level_badge(self, obj):
        """Badge for log level."""
        level = (obj.level or "error").lower()
        css_class = f"stacktrace-level stacktrace-level-{level}"
        return format_html(
            '<span class="{}">{}</span>',
            css_class,
            level.upper(),
        )

    @admin.display(description="Events", ordering="occurrence_count")
    def events_count(self, obj):
        """Formatted event count."""
        count = obj.occurrence_count or 0
        formatted = format_count(count)
        css_class = "stacktrace-count stacktrace-count-high" if count >= 1000 else "stacktrace-count"
        return format_html('<span class="{}">{}</span>', css_class, formatted)

    @admin.display(description="Time", ordering="last_seen_at")
    def time_info(self, obj):
        """Last seen time and age."""
        now = datetime.now(timezone.utc)
        last_seen_ago = timesince(obj.last_seen_at, now) if obj.last_seen_at else "-"
        age = timesince(obj.created_at, now) if obj.created_at else "-"

        return format_html(
            '<div class="stacktrace-timestamp">{} ago</div>'
            '<div class="stacktrace-timestamp">{} old</div>',
            last_seen_ago,
            age,
        )

    @admin.display(description="Logger")
    def logger_display(self, obj):
        """Logger name with server info."""
        logger = obj.logger or "root"
        server = obj.server_name or ""

        if server:
            return format_html(
                '<div class="stacktrace-logger">{}</div>'
                '<div class="stacktrace-server">{}</div>',
                logger,
                server,
            )
        return format_html('<span class="stacktrace-logger">{}</span>', logger)

    @admin.display(description="Request")
    def request_info(self, obj):
        """Request method and path."""
        method = obj.request_method or ""
        path = obj.request_path or ""

        if not method and not path:
            return "-"

        path_display = path[:40] + "..." if len(path) > 40 else path

        if method:
            return format_html(
                "<div><strong>{}</strong></div>" '<div class="stacktrace-path">{}</div>',
                method,
                path_display,
            )
        return format_html('<span class="stacktrace-path">{}</span>', path_display)

    # -------------------- Detail View Methods --------------------

    @admin.display(description="Tags")
    def tags_display(self, obj):
        """Display tags extracted from context."""
        if not isinstance(obj.context, dict):
            return "-"

        tags = []

        # Extract common tags
        tags.append(("level", obj.level or "error"))
        tags.append(("logger", obj.logger or "root"))

        contexts = obj.context.get("contexts", {})

        # Runtime info
        runtime = contexts.get("runtime", {})
        if runtime:
            runtime_str = f"{runtime.get('name', '')} {runtime.get('version', '')}"
            tags.append(("runtime", runtime_str.strip()))

        # Django info
        django_ctx = contexts.get("django", {})
        if django_ctx:
            tags.append(("django", django_ctx.get("app_version", "")))

        # Server
        if obj.server_name:
            tags.append(("server_name", obj.server_name))

        # Build HTML
        html_parts = []
        for key, value in tags:
            if value:
                html_parts.append(
                    f'<span style="display: inline-block; margin: 2px 4px 2px 0; '
                    f"padding: 4px 8px; background: var(--darkened-bg); "
                    f'border: 1px solid var(--hairline-color); font-size: 12px;">'
                    f"<strong>{escape(key)}</strong>: {escape(str(value))}</span>"
                )

        return mark_safe("".join(html_parts)) if html_parts else "-"

    @admin.display(description="Exception")
    def exception_display(self, obj):
        """Render raw traceback and exception frames for all exceptions in values."""
        html_parts = []

        # First show raw traceback from CrashEvent.traceback or context
        raw_tb = None
        if obj.traceback:
            raw_tb = obj.traceback
        elif isinstance(obj.context, dict):
            raw_tb = obj.context.get("contexts", {}).get("traceback", {}).get("raw")

        if raw_tb:
            html_parts.append(
                '<div style="margin-bottom: 16px;">'
                '<div style="font-weight: bold; margin-bottom: 8px;">Raw Traceback:</div>'
                '<pre style="white-space: pre-wrap; overflow-x: auto; '
                "max-height: 400px; padding: 10px; font-family: monospace; font-size: 12px; "
                f'background: var(--darkened-bg); border: 1px solid var(--hairline-color);">{escape(raw_tb)}</pre>'
                "</div>"
            )

        if not isinstance(obj.context, dict):
            return mark_safe("".join(html_parts)) if html_parts else "-"

        exception_data = obj.context.get("exception", {})
        values = exception_data.get("values", [])

        if not values:
            return mark_safe("".join(html_parts)) if html_parts else "-"

        # Section header for frames
        html_parts.append(
            '<div style="font-weight: bold; margin-bottom: 8px;">Exception Frames:</div>'
        )

        for idx, exc_value in enumerate(values):
            exc_type = exc_value.get("type", "Exception")
            exc_msg = exc_value.get("value", "")
            exc_module = exc_value.get("module", "")
            stacktrace = exc_value.get("stacktrace", {})
            frames = stacktrace.get("frames", [])

            # Exception header
            html_parts.append(
                f'<div style="margin-bottom: 16px; padding: 12px; '
                f'background: var(--darkened-bg); border: 1px solid var(--hairline-color);">'
            )

            # Exception title
            full_type = f"{exc_module}.{exc_type}" if exc_module else exc_type
            html_parts.append(
                f'<div style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">'
                f"{escape(full_type)}</div>"
            )

            # Exception message
            if exc_msg:
                html_parts.append(
                    f'<div style="color: var(--body-quiet-color); margin-bottom: 12px;">'
                    f"{escape(exc_msg)}</div>"
                )

            # Frames (most recent call last - reverse for display)
            if frames:
                html_parts.append(
                    '<div style="font-size: 12px; color: var(--body-quiet-color); '
                    'margin-bottom: 8px;">Stack trace (most recent call last):</div>'
                )

                for frame in frames:
                    filename = frame.get("filename", "")
                    abs_path = frame.get("abs_path", filename)
                    function = frame.get("function", "")
                    lineno = frame.get("lineno", "")
                    context_line = frame.get("context_line", "")

                    # Frame container
                    html_parts.append(
                        '<div style="margin: 4px 0; padding: 8px; '
                        "border-left: 3px solid var(--hairline-color); "
                        'background: var(--body-bg);">'
                    )

                    # File and function
                    html_parts.append(
                        f'<div style="font-family: monospace; font-size: 12px;">'
                        f"<strong>{escape(filename)}</strong> in "
                        f"<strong>{escape(function)}</strong> at line "
                        f"<strong>{escape(str(lineno))}</strong></div>"
                    )

                    # Context line (the actual code)
                    if context_line:
                        html_parts.append(
                            f'<div style="font-family: monospace; font-size: 11px; '
                            f"margin-top: 4px; padding: 4px; background: var(--darkened-bg); "
                            f'color: var(--error-fg);">{escape(context_line)}</div>'
                        )

                    html_parts.append("</div>")

            html_parts.append("</div>")

            # Separator between multiple exceptions
            if idx < len(values) - 1:
                html_parts.append(
                    '<div style="text-align: center; color: var(--body-quiet-color); '
                    'margin: 8px 0;">Caused by:</div>'
                )

        return mark_safe("".join(html_parts))

    @admin.display(description="Request Details")
    def request_display(self, obj):
        """Display request information."""
        if not isinstance(obj.context, dict):
            return "-"

        request_data = obj.context.get("request", {})
        if not request_data:
            return "-"

        html_parts = ['<table style="width: 100%; border-collapse: collapse;">']

        fields = [
            ("URL", request_data.get("url")),
            ("Method", request_data.get("method")),
            ("Query String", request_data.get("query_string")),
            ("Headers", request_data.get("headers")),
            ("Data", request_data.get("data")),
            ("Environment", request_data.get("env")),
        ]

        for label, value in fields:
            if value:
                if isinstance(value, dict):
                    value_str = json.dumps(value, indent=2)
                    value_html = (
                        f'<pre style="margin: 0; white-space: pre-wrap; '
                        f'font-family: monospace; font-size: 12px;">{escape(value_str)}</pre>'
                    )
                else:
                    value_html = escape(str(value))

                html_parts.append(
                    f'<tr style="border-bottom: 1px solid var(--hairline-color);">'
                    f'<td style="padding: 8px; font-weight: bold; width: 120px; '
                    f'vertical-align: top;">{escape(label)}</td>'
                    f'<td style="padding: 8px;">{value_html}</td></tr>'
                )

        html_parts.append("</table>")
        return mark_safe("".join(html_parts))

    @admin.display(description="User Details")
    def user_display(self, obj):
        """Display user information."""
        if not isinstance(obj.context, dict):
            return "-"

        user_data = obj.context.get("user", {})
        if not user_data:
            return "-"

        html_parts = ['<table style="width: 100%; border-collapse: collapse;">']

        fields = [
            ("ID", user_data.get("id")),
            ("Username", user_data.get("username_field_value")),
            ("IP Address", user_data.get("ip_address")),
        ]

        for label, value in fields:
            if value:
                html_parts.append(
                    f'<tr style="border-bottom: 1px solid var(--hairline-color);">'
                    f'<td style="padding: 8px; font-weight: bold; width: 120px;">{escape(label)}</td>'
                    f'<td style="padding: 8px;">{escape(str(value))}</td></tr>'
                )

        html_parts.append("</table>")
        return mark_safe("".join(html_parts))

    @admin.display(description="Full Context")
    def context_display(self, obj):
        """Render full JSON context with copy button."""
        try:
            data = obj.context
            if isinstance(data, str):
                data = json.loads(data)
            payload_str = json.dumps(data, indent=2, sort_keys=True)
        except Exception:
            payload_str = str(obj.context)

        # Generate unique ID for this textarea
        textarea_id = f"context-json-{obj.pk}"

        html = f"""
        <div style="position: relative;">
            <button type="button" onclick="
                var text = document.getElementById('{textarea_id}').textContent;
                navigator.clipboard.writeText(text).then(function() {{
                    alert('Copied to clipboard!');
                }});
            " style="
                position: absolute;
                top: 8px;
                right: 8px;
                padding: 4px 12px;
                background: var(--button-bg);
                color: var(--button-fg);
                border: 1px solid var(--hairline-color);
                cursor: pointer;
                font-size: 12px;
            ">Copy JSON</button>
            <pre id="{textarea_id}" style="
                white-space: pre-wrap;
                overflow-x: auto;
                max-height: 600px;
                padding: 10px;
                padding-top: 40px;
                font-family: monospace;
                font-size: 12px;
                background: var(--darkened-bg);
                border: 1px solid var(--hairline-color);
            ">{escape(payload_str)}</pre>
        </div>
        """

        return mark_safe(html)
