from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThanOrEqual


class Incident(models.Model):
    class Category(models.TextChoices):
        LOST_OBJECT = "objeto_extraviado", "Objeto extraviado"
        INFRASTRUCTURE_DAMAGE = "dano_infraestructura", "Daño a infraestructura"
        MISCONDUCT = "comportamiento_indebido", "Comportamiento indebido"
        MEDICAL_EMERGENCY = "emergencia_medica", "Emergencia médica"
        OTHER = "otro", "Otro"

    description = models.TextField(
        validators=[MinLengthValidator(
            10, message="La descripción debe tener al menos 10 caracteres."
        )],
        error_messages={"blank": "La descripción debe tener al menos 10 caracteres."},
    )
    category = models.CharField(max_length=23, choices=Category.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False
    )

    def clean(self):
        super().clean()
        if self.description is not None:
            self.description = self.description.strip()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(category__in=[
                    "objeto_extraviado", "dano_infraestructura",
                    "comportamiento_indebido", "emergencia_medica", "otro",
                ]),
                name="incident_valid_category",
            ),
            models.CheckConstraint(
                condition=GreaterThanOrEqual(Length(Trim("description")), 10),
                name="incident_description_min_length",
                violation_error_message="La descripción debe tener al menos 10 caracteres.",
            ),
        ]
