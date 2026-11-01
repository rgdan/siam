from django.db import migrations, models


def preserve_photo_order(apps, schema_editor):
    Photo = apps.get_model("collection_integrity", "Photo")
    photos = Photo.objects.using(schema_editor.connection.alias)
    previous_piece = None
    position = 0
    for photo_id, piece_id in photos.order_by("piece_id", "id").values_list("id", "piece_id").iterator():
        if piece_id != previous_piece:
            previous_piece = piece_id
            position = 0
        photos.filter(pk=photo_id).update(position=position)
        position += 1


class Migration(migrations.Migration):
    dependencies = [("collection_integrity", "0004_move_history_to_audit")]

    operations = [
        migrations.AddField(
            model_name="photo", name="position", field=models.PositiveIntegerField(default=0)
        ),
        migrations.RunPython(preserve_photo_order, migrations.RunPython.noop),
        migrations.AlterModelOptions(name="photo", options={"ordering": ["position", "id"]}),
    ]
