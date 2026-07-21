from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collections', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='concept',
            old_name='variables',
            new_name='dimensiones',
        ),
        migrations.RenameField(
            model_name='concept',
            old_name='variables_compatibles',
            new_name='dimensiones_compatibles',
        ),
    ]
