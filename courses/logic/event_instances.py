from courses.models import Exercise


def get_exercises_from(template, course=None, public_only=False):
    exercises = Exercise.objects.base_exercises()
    if public_only:
        exercises = exercises.public()
    if course is not None:
        exercises = exercises.filter(course=course)

    picked_exercises = []
    for rule in template.rules.all():
        rule_qs = exercises.satisfying(rule)

        picked_exercise = rule_qs.exclude(
            pk__in=[e.pk for e in picked_exercises]  # don't pick same exercise again
        ).get_random()
        picked_exercises.append(picked_exercise)

    return picked_exercises
