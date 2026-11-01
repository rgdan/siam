
import uuid
from decimal import Decimal

import django.core.validators
from django.db import migrations, models


def populate_identifiers(apps, schema_editor):
    Piece = apps.get_model("collection_integrity", "Piece")
    for piece in Piece.objects.using(schema_editor.connection.alias).all().iterator():
        piece.identifier = uuid.uuid4()
        if piece.state not in ["stored", "displayed"]:
            piece.state = "stored"
        piece.save(
            using=schema_editor.connection.alias, update_fields=["identifier", "state"]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("collection_integrity", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="mime_type",
            field=models.CharField(default="image/jpeg", max_length=30),
        ),
        migrations.AddField(
            model_name="piece",
            name="author_maker",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="piece",
            name="date_period",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="piece",
            name="distinguishing_features",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="piece",
            name="identifier",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(populate_identifiers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="piece",
            name="identifier",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="piece",
            name="inscriptions_marks",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="piece",
            name="location",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="piece",
            name="materials_techniques",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="piece",
            name="measurement_unit",
            field=models.CharField(blank=True, max_length=5),
        ),
        migrations.AddField(
            model_name="piece",
            name="measurement_value",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=14,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0.0001"))
                ],
            ),
        ),
        migrations.AddField(
            model_name="piece",
            name="object_type",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="piece",
            name="subject",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="piece",
            name="state",
            field=models.CharField(default="stored", max_length=40),
        ),
    ]
