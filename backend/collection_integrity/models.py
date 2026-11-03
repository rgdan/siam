import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Piece(models.Model):
    identifier = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    collection = models.CharField(max_length=200, blank=True)
    object_type = models.TextField(blank=True)
    materials_techniques = models.TextField(blank=True)
    measurement_value = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    measurement_unit = models.CharField(max_length=5, blank=True)
    inscriptions_marks = models.TextField(blank=True)
    distinguishing_features = models.TextField(blank=True)
    subject = models.TextField(blank=True)
    date_period = models.TextField(blank=True)
    author_maker = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200)
    state = models.CharField(
        max_length=40,
        default="stored",
        choices=[("stored", "En almacenamiento"), ("displayed", "En exhibici\u00f3n")],
    )
    decommissioned = models.BooleanField(default=False)
    loan_to = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(state__in=["stored", "displayed"]),
                name="piece_valid_state",
            ),
            models.CheckConstraint(
                condition=models.Q(state="stored", location="")
                | (models.Q(state="displayed") & ~models.Q(location="")),
                name="piece_current_location",
            ),
        ]


class Photo(models.Model):
    piece = models.ForeignKey(Piece, related_name="photos", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    content = models.BinaryField()
    mime_type = models.CharField(max_length=30, default="image/jpeg")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
