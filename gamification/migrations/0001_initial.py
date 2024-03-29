# Generated by Django 4.1 on 2022-08-24 13:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BadgeDefinition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="GamificationContext",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("object_id", models.TextField()),
                ("is_default_context", models.BooleanField(default=False)),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Goal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.TextField()),
                (
                    "context",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="goals",
                        to="gamification.gamificationcontext",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GoalLevel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("requirements", models.JSONField(default=dict)),
                ("level_value", models.PositiveIntegerField()),
                ("points_awarded", models.PositiveIntegerField()),
                (
                    "badges_awarded",
                    models.ManyToManyField(
                        blank=True,
                        related_name="awarded_in_goal_levels",
                        to="gamification.badgedefinition",
                    ),
                ),
                (
                    "goal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="levels",
                        to="gamification.goal",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="badgedefinition",
            name="context",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="badges",
                to="gamification.gamificationcontext",
            ),
        ),
        migrations.CreateModel(
            name="Badge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                (
                    "badge_definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="badges",
                        to="gamification.badgedefinition",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="badges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ActionDefinition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            (
                                "TURN_IN_PRACTICE_PARTICIPATION",
                                "TURN_IN_PRACTICE_PARTICIPATION",
                            ),
                            ("SUBMIT_EXERCISE_SOLUTION", "SUBMIT_EXERCISE_SOLUTION"),
                            (
                                "EXERCISE_SOLUTION_APPROVED",
                                "EXERCISE_SOLUTION_APPROVED",
                            ),
                        ],
                        max_length=100,
                    ),
                ),
                ("parameters", models.JSONField(default=dict)),
                ("points_awarded", models.PositiveIntegerField()),
                (
                    "badges_awarded",
                    models.ManyToManyField(
                        blank=True,
                        related_name="awarded_in_actions",
                        to="gamification.badgedefinition",
                    ),
                ),
                (
                    "context",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actions",
                        to="gamification.gamificationcontext",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Action",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                (
                    "definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actions",
                        to="gamification.actiondefinition",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
