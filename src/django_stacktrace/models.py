import uuid

from django.db import models


class CrashEvent(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen_at = models.DateTimeField(auto_now=True, db_index=True)
    occurrence_count = models.PositiveIntegerField(default=1)
    level = models.CharField(max_length=32, db_index=True, blank=True)
    logger = models.CharField(max_length=255, db_index=True, blank=True)
    error_type = models.CharField(max_length=255, db_index=True, blank=True)
    message = models.TextField(blank=True)
    request_path = models.CharField(max_length=2048, db_index=True, blank=True)
    request_method = models.CharField(max_length=16, blank=True)
    user_identifier = models.CharField(max_length=255, db_index=True, blank=True)
    remote_addr = models.CharField(max_length=64, blank=True)
    traceback = models.TextField()
    traceback_hash = models.CharField(max_length=64, unique=True)
    context = models.JSONField(default=dict)
    server_name = models.CharField(max_length=255, db_index=True, blank=True)
    culprit = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ["-last_seen_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["last_seen_at"]),
            models.Index(fields=["level"]),
            models.Index(fields=["logger"]),
            models.Index(fields=["error_type"]),
            models.Index(fields=["request_path"]),
            models.Index(fields=["user_identifier"]),
        ]

    def __str__(self) -> str:
        return f"{self.level or 'ERROR'} {self.error_type or 'Exception'} (x{self.occurrence_count})"
