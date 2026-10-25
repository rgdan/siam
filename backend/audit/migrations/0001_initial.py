import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEntry",
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
                ("role", models.CharField(blank=True, max_length=25)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("create", "Crear"),
                            ("modify", "Modificar"),
                            ("decommission", "Dar de baja"),
                            ("sensitive_read", "Lectura sensible"),
                            ("login", "Inicio de sesión"),
                            ("failed_login", "Inicio fallido"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("entity", models.CharField(db_index=True, max_length=100)),
                ("entity_id", models.CharField(blank=True, max_length=255)),
                ("changes", models.JSONField(default=dict)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp", "-pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            (
                                "action_type__in",
                                [
                                    "create",
                                    "modify",
                                    "decommission",
                                    "sensitive_read",
                                    "login",
                                    "failed_login",
                                ],
                            )
                        ),
                        name="audit_valid_action",
                    )
                ],
            },
        ),
    ]
