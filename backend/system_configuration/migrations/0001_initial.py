from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Parameter",
            fields=[
                (
                    "key",
                    models.CharField(max_length=40, primary_key=True, serialize=False),
                ),
                ("value", models.JSONField()),
            ],
        ),
    ]
