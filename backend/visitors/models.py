from django.conf import settings
from django.db import models


class VisitorEntry(models.Model):
    class AgeGroup(models.TextChoices):
        ADULT = "mayor", "Mayor"
        MINOR = "menor", "Menor"

    class Nationality(models.TextChoices):
        NATIONAL = "nacional", "Nacional"
        FOREIGN = "extranjero", "Extranjero"

    class Sex(models.TextChoices):
        MALE = "masculino", "Masculino"
        FEMALE = "femenino", "Femenino"

    age_group = models.CharField(max_length=5, choices=AgeGroup.choices)
    nationality = models.CharField(max_length=10, choices=Nationality.choices)
    sex = models.CharField(max_length=9, choices=Sex.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(age_group__in=["mayor", "menor"]),
                name="visitor_entry_valid_age_group",
            ),
            models.CheckConstraint(
                condition=models.Q(nationality__in=["nacional", "extranjero"]),
                name="visitor_entry_valid_nationality",
            ),
            models.CheckConstraint(
                condition=models.Q(sex__in=["masculino", "femenino"]),
                name="visitor_entry_valid_sex",
            ),
        ]
