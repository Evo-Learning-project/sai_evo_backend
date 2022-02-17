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

        rule_picked_exercises = rule_qs.exclude(
            pk__in=[e.pk for e in picked_exercises]  # don't pick same exercise again
        ).get_random(amount=rule.amount)
        picked_exercises.extend(rule_picked_exercises)

    return picked_exercises
