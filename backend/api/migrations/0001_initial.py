from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('full_name', models.CharField(max_length=200)),
                ('role', models.CharField(choices=[('guarda', 'Guarda'), ('coordinador', 'Coordinador'), ('museologo', 'Museólogo'), ('administrador_general', 'Administrador general'), ('administrador_sistema', 'Administrador de sistema')], max_length=25)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('role__in', ['guarda', 'coordinador', 'museologo', 'administrador_general', 'administrador_sistema'])), name='user_valid_role')],
            },
        ),
    ]
