# Generated by Django 4.0.7 on 2022-10-19 12:41

import courses.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0076_eventparticipationslot_event_participation_unique_base_slot_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExerciseTestCaseAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment', models.FileField(blank=True, null=True, upload_to=courses.models.get_testcase_attachment_path)),
                ('testcase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='courses.exercisetestcase')),
            ],
        ),
    ]