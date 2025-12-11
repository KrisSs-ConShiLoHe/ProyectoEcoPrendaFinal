# Generated manually to fix logro_id type mismatch

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0009_auto_20251211_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuariologro',
            name='logro',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='App.logro'),
        ),
    ]
