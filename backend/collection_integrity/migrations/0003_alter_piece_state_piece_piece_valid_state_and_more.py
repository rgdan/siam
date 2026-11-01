
from django.db import migrations, models


def clear_legacy_display_without_location(apps, schema_editor):
    Piece = apps.get_model("collection_integrity", "Piece")
    Piece.objects.using(schema_editor.connection.alias).filter(
        state="displayed", location=""
    ).update(state="stored")


class Migration(migrations.Migration):
    dependencies = [
        (
            "collection_integrity",
            "0002_photo_mime_type_piece_author_maker_piece_date_period_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            clear_legacy_display_without_location, migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="piece",
            name="state",
            field=models.CharField(
                choices=[
                    ("stored", "En almacenamiento"),
                    ("displayed", "En exhibición"),
                ],
                default="stored",
                max_length=40,
            ),
        ),
        migrations.AddConstraint(
            model_name="piece",
            constraint=models.CheckConstraint(
                condition=models.Q(("state__in", ["stored", "displayed"])),
                name="piece_valid_state",
            ),
        ),
        migrations.AddConstraint(
            model_name="piece",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("location", ""), ("state", "stored")),
                    models.Q(
                        ("state", "displayed"),
                        models.Q(("location", ""), _negated=True),
                    ),
                    _connector="OR",
                ),
                name="piece_current_location",
            ),
        ),
    ]
