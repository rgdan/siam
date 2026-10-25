from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("La bitácora es de solo lectura.")

    def delete(self):
        raise ValidationError("La bitácora es de solo lectura.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("La bitácora es de solo lectura.")


class AuditEntry(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Crear"
        MODIFY = "modify", "Modificar"
        DECOMMISSION = "decommission", "Dar de baja"
        SENSITIVE_READ = "sensitive_read", "Lectura sensible"
        LOGIN = "login", "Inicio de sesión"
        FAILED_LOGIN = "failed_login", "Inicio fallido"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT
    )
    role = models.CharField(max_length=25, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    action_type = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    entity = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict)
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        ordering = ["-timestamp", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    action_type__in=[
                        "create",
                        "modify",
                        "decommission",
                        "sensitive_read",
                        "login",
                        "failed_login",
                    ]
                ),
                name="audit_valid_action",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("La bitácora es de solo lectura.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("La bitácora es de solo lectura.")
