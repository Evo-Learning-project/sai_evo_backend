# Generated by Django 4.0.8 on 2022-11-28 14:31

import course_tree.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_tree', '0003_filenode_thumbnail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filenode',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=course_tree.models.get_filenode_file_path),
        ),
    ]
