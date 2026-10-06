from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca', '0003_prestamo_renovado'),
    ]

    operations = [
        migrations.AddField(
            model_name='libro',
            name='anho',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='libro',
            name='editorial',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
