from decimal import Decimal
from courses.models import Exercise, Course
from django.db.models import Max, F


def migrate_choice_correctness():
    """
    Migrates all exercises' choices to new correctness system: in exercises
    with a single correct choice, that choice gets 100% correctness; in ones
    with multiple selectable choices, they all get an equal share of
    correctness, and the others get a -10% penalty (arbitrarily chosen)
    """

    for course in Course.objects.all():
        mcs_exercises = course.exercises.filter(
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE
        )
        for exercise in mcs_exercises:
            if exercise.choices.exists():
                max_score = (exercise.choices.aggregate(Max("correctness_percentage")))[
                    "correctness_percentage__max"
                ] or 1

                for choice in exercise.choices.all():
                    choice.correctness_percentage = (
                        choice.correctness_percentage / Decimal(max_score) * 100
                    )
                    choice.save()

        mcm_exercises = course.exercises.filter(
            exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE
        )
        for exercise in mcm_exercises:
            if exercise.choices.exists():
                correct_choices = exercise.choices.filter(correctness_percentage__gt=0)
                correct_choices.update(
                    correctness_percentage=100
                    / (correct_choices.count() or exercise.choices.count())
                )
                exercise.choices.filter(correctness_percentage__lte=0).update(
                    correctness_percentage=-10
                )
