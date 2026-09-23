from django.contrib.postgres.fields import JSONField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collections', '0002_rename_variables_to_dimensiones'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='limitations',
            field=JSONField(default=list),
        ),
        migrations.AddField(
            model_name='concept',
            name='frecuencia',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='concept',
            name='unidad',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='concept',
            name='sample_questions',
            field=JSONField(default=list),
        ),
        migrations.AddField(
            model_name='concept',
            name='limitations',
            field=JSONField(default=list),
        ),
    ]
