# Generated by Django 4.0.4 on 2022-05-26 18:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0059_delete_eventinstance'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ParticipationAssessmentSlot',
        ),
    ]