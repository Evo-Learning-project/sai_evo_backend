# Generated by Django 4.0.1 on 2022-02-14 14:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0017_rename_state_event__event_state_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exercise',
            old_name='tags',
            new_name='public_tags',
        ),
    ]