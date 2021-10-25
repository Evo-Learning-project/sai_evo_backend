def apply_grading_rule(assigned_exercise):
    """
    Takes in an AssignedExercise model instance (representing an exercise assigned to a user
    and the answer given to that exercise) and an ExerciseGradingRule.

    Returns the score that results in applying the given rule with the given answer(s).
    """

    from courses.models import AssignedExercise, Exercise, ExerciseGradingRule

    try:
        rule = assigned_exercise.event.grading_rules.get(
            exercise=assigned_exercise.exercise
        )
    except ExerciseGradingRule.DoesNotExist:
        # TODO get default rule
        pass

    if (
        assigned_exercise.exercise.exercise_type == Exercise.OPEN_ANSWER
        or assigned_exercise.exercise.exercise_type == Exercise.ATTACHMENT
    ):
        return None

    if assigned_exercise.exercise.exercise_type == Exercise.JS:
        # TODO implement grading for js exercises
        pass

    if (
        assigned_exercise.exercise.exercise_type
        == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE
    ):
        if assigned_exercise.selected_choice is None:
            return rule.points_for_blank
        return (
            rule.points_for_correct
            if assigned_exercise.selected_choice.correct
            else rule.points_for_incorrect
        )

    participation = assigned_exercise.participation

    # for composed exercises, the score is the sum of the sub-exercises
    sub_exercises_score = sum(
        [
            apply_grading_rule(rule, participation.assigned_exercises.get(exercise=e))
            for e in assigned_exercise.exercise.sub_exercises.all()
        ]
    )

    return (
        0
        if rule.minimum_score_threshold is not None
        and sub_exercises_score < rule.minimum_score_threshold
        else sub_exercises_score
    )
