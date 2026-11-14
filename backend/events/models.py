from django.conf import settings

from django.db import models


# Representa los eventos registrados en el museo.
class Evento(models.Model):
    class Tipo(models.TextChoices):
        PUBLICO = "publico", "Público"
        PRIVADO = "privado", "Privado"

    class Estado(models.TextChoices):
        PROGRAMADO = "programado", "Programado"
        CANCELADO = "cancelado", "Cancelado"

    fecha = models.DateTimeField()
    descripcion = models.CharField(max_length=500)
    ubicacion = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    asistentes_esperados = models.PositiveIntegerField()
    asistentes_reales = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PROGRAMADO,
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_creados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["fecha"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(asistentes_esperados__gte=1),
                name="evento_asistentes_esperados_positivos",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(asistentes_reales__isnull=True)
                    | models.Q(asistentes_reales__gte=0)
                ),
                name="evento_asistentes_reales_validos",
            ),
        ]

    def __str__(self):
        return f"{self.descripcion[:50]} - {self.fecha}"
