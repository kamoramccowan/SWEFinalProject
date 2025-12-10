import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_usersettings_allowed_sender_user_ids_challengeinvite'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='usersettings',
            name='theme',
            field=models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('high-contrast', 'High Contrast')], default='light', max_length=32),
        ),
    ]
