def create_exercise_solutions():
    """
    Creates an ExerciseSolution object for each exercise that has a solution
    """
    from courses.models import Course, ExerciseSolution

    for c in Course.objects.all():
        exercises = c.exercises.exclude(solution__exact="")
        for e in exercises:
            ExerciseSolution.objects.create(
                exercise=e,
                content=e.solution,
                state=ExerciseSolution.PUBLISHED,
                user=e.creator,
            )
