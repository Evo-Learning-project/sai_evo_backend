# Generated by Django 4.1 on 2022-09-02 10:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "gamification",
            "0008_rename_requirements_goallevel_action_requirements_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="actiondefinition",
            name="action_code",
            field=models.CharField(
                choices=[
                    (
                        "TURN_IN_PRACTICE_PARTICIPATION",
                        "TURN_IN_PRACTICE_PARTICIPATION",
                    ),
                    ("SUBMIT_EXERCISE_SOLUTION", "SUBMIT_EXERCISE_SOLUTION"),
                    (
                        "SUBMIT_FIRST_EXERCISE_SOLUTION",
                        "SUBMIT_FIRST_EXERCISE_SOLUTION",
                    ),
                    ("EXERCISE_SOLUTION_APPROVED", "EXERCISE_SOLUTION_APPROVED"),
                    ("EXERCISE_SOLUTION_UPVOTED", "EXERCISE_SOLUTION_UPVOTED"),
                    ("EXERCISE_SOLUTION_DOWNVOTED", "EXERCISE_SOLUTION_DOWNVOTED"),
                    (
                        "EXERCISE_SOLUTION_UPVOTE_DELETED",
                        "EXERCISE_SOLUTION_UPVOTE_DELETED",
                    ),
                    (
                        "EXERCISE_SOLUTION_DOWNVOTE_DELETED",
                        "EXERCISE_SOLUTION_DOWNVOTE_DELETED",
                    ),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="actiondefinition",
            name="reputation_awarded",
            field=models.IntegerField(),
        ),
    ]
