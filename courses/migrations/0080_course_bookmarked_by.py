# Generated by Django 4.0.8 on 2023-01-01 23:14

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0079_remove_event_locked_by_remove_exercise_locked_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='bookmarked_by',
            field=models.ManyToManyField(blank=True, related_name='bookmarked_courses', to=settings.AUTH_USER_MODEL),
        ),
    ]