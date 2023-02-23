def get_cloze_sub_exercises_appearing_in_exercise_text(exercise):
    """
    As of now, cloze exercises (i.e. type Exercise.COMPLETION) work by including
    the id of sub-exercises enclosed in double brackets, e.g. `[[123]]`.
    The frontend replaces these placeholders with a select component to pick the
    corresponding choice.

    Currently, when the placeholder for a sub-exercise is deleted in the text editor,
    that sub-exercise becomes un-answerable. Therefore, assessment needs to account
    for that and avoid counting those exercises.

    This function takes in a cloze exercise and returns the list of sub-exercises
    for which the corresponding placeholder appears in the exercise text
    """
    return [e for e in exercise.sub_exercises.all() if f"[[{e.pk}]]" in exercise.text]
