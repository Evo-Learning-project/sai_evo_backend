# Generated by Django 3.2.20 on 2023-12-05 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0088_alter_event_visibility'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='retriability',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Not retriable'), (1, 'Retriable')], default=0),
        ),
    ]
