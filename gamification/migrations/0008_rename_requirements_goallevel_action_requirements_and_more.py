# Generated by Django 4.1 on 2022-08-26 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("gamification", "0007_rename_action_actiondefinition_action_code"),
    ]

    operations = [
        migrations.RenameField(
            model_name="goallevel",
            old_name="requirements",
            new_name="action_requirements",
        ),
        migrations.AlterField(
            model_name="goallevelactiondefinitionrequirement",
            name="goal_level",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="requirements",
                to="gamification.goallevel",
            ),
        ),
        migrations.AlterField(
            model_name="goalprogress",
            name="current_level",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="current_in_progresses",
                to="gamification.goallevel",
            ),
        ),
    ]