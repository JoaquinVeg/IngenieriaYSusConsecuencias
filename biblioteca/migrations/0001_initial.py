from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Libro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=50, unique=True)),
                ('titulo', models.CharField(max_length=200)),
                ('autor', models.CharField(max_length=100)),
                ('editorial', models.CharField(blank=True, max_length=100, null=True)),
                ('anho', models.IntegerField(blank=True, null=True)),
                ('estado', models.CharField(default='Disponible', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=12, unique=True)),
                ('nombre', models.CharField(max_length=100)),
                ('correo', models.EmailField(max_length=254)),
                ('tipo', models.CharField(choices=[('Estudiante', 'Estudiante'), ('Docente', 'Docente')], max_length=20)),
                ('multa_pendiente', models.BooleanField(default=False)),
            ],
        ),
    ]
