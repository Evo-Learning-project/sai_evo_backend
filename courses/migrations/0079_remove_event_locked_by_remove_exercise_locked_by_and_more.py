# Generated by Django 4.0.7 on 2022-11-01 13:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0078_event_last_heartbeat_exercise_last_heartbeat'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='locked_by',
        ),
        migrations.RemoveField(
            model_name='exercise',
            name='locked_by',
        ),
        migrations.AddField(
            model_name='event',
            name='_locked_by',
            field=models.ForeignKey(blank=True, db_column='locked_by', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='exercise',
            name='_locked_by',
            field=models.ForeignKey(blank=True, db_column='locked_by', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
    ]