from courses.models import EventTemplateRule, Exercise


def get_exercises_from(template, course=None, pool=None):
    exercises = Exercise.objects.base_exercises()
    if course is not None:
        exercises = exercises.filter(course=course)
    if pool is not None:
        exercises = exercises.filter(pk__in=pool)

    picked_exercises = []
    for rule in template.rules.all():
        rule_qs = exercises.satisfying(rule)

        # picked_exercise = (
        #     rule_qs
        #     # .distinct()  # if more than one tag match, an item may be returned more than once
        #     .order_by("?")  # shuffle entries
        #     .exclude(
        #         pk__in=[e.pk for e in picked_exercises]
        #     )  # avoid picking same exercises more than once
        #     .first()  # get the first item in the queryset
        # )

        picked_exercise = rule_qs.get_random(exclude=picked_exercises)
        picked_exercises.append(picked_exercise)

    return picked_exercises
