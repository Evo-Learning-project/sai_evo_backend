# Generated by Django 4.0.7 on 2022-10-01 09:21

import demo_mode.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo_mode', '0002_alter_demoinvitation_main_invitee_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='demoinvitation',
            name='duration_hours',
        ),
        migrations.AlterField(
            model_name='demoinvitation',
            name='other_invitees_emails',
            field=models.JSONField(blank=True, default=list, validators=[demo_mode.models.validate_list_of_emails]),
        ),
    ]