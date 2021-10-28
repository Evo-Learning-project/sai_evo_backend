# Generated by Django 3.2.8 on 2021-10-26 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_auto_20211026_2350'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventtemplaterule',
            name='position',
        ),
        migrations.AddField(
            model_name='eventtemplaterule',
            name='slot_number',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]