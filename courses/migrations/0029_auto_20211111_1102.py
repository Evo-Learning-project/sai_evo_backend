# Generated by Django 3.2.9 on 2021-11-11 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0028_auto_20211111_1031'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exercise',
            name='draft',
        ),
        migrations.AddField(
            model_name='exercise',
            name='skip_if_timeout',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='exercise',
            name='state',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Draft'), (1, 'Private'), (2, 'Public')], default=0),
        ),
        migrations.AddField(
            model_name='exercise',
            name='time_to_complete',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]