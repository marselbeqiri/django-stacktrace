from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CrashEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("level", models.CharField(blank=True, db_index=True, max_length=32)),
                ("logger", models.CharField(blank=True, db_index=True, max_length=255)),
                (
                    "error_type",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
                ("message", models.TextField(blank=True)),
                (
                    "request_path",
                    models.CharField(blank=True, db_index=True, max_length=2048),
                ),
                ("request_method", models.CharField(blank=True, max_length=16)),
                (
                    "user_identifier",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
                ("remote_addr", models.CharField(blank=True, max_length=64)),
                ("user_agent", models.TextField(blank=True)),
                (
                    "traceback_hash",
                    models.CharField(blank=True, db_index=True, max_length=64),
                ),
                ("payload", models.JSONField(default=dict)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="crashevent",
            index=models.Index(
                fields=["created_at"], name="django_cra_created_f746c1_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="crashevent",
            index=models.Index(fields=["level"], name="django_cra_level_3c9407_idx"),
        ),
        migrations.AddIndex(
            model_name="crashevent",
            index=models.Index(fields=["logger"], name="django_cra_logger_7ae3d1_idx"),
        ),
        migrations.AddIndex(
            model_name="crashevent",
            index=models.Index(
                fields=["error_type"], name="django_cra_error_t_75f241_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="crashevent",
            index=models.Index(
                fields=["request_path"], name="django_cra_request_a77d3f_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="crashevent",
            index=models.Index(
                fields=["user_identifier"], name="django_cra_user_id_714759_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="crashevent",
            index=models.Index(
                fields=["traceback_hash"], name="django_cra_traceba_0a37ef_idx"
            ),
        ),
    ]
