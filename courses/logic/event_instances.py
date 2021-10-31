from courses.models import EventTemplateRule, Exercise


def get_exercises_from(template, course=None, pool=None):
    exercises = Exercise.objects.base_exercises()
    if course is not None:
        exercises = exercises.filter(course=course)
    if pool is not None:
        exercises = exercises.filter(pk__in=pool)

    picked_exercises = []
    for rule in template.rules.all():
        if rule.rule_type == EventTemplateRule.ID_BASED:
            rule_qs = exercises.filter(pk__in=[e.pk for e in rule.exercises.all()])
        else:  # tag-based rule
            rule_qs = exercises
            for clause in rule.clauses.all():
                rule_qs = rule_qs.filter(tags__in=[t for t in clause.tags.all()])

        picked_exercise = (
            rule_qs.distinct()  # if more than one tag match, an item may be returned more than once
            .order_by("?")  # shuffle entries
            .exclude(
                pk__in=[e.pk for e in picked_exercises]
            )  # avoid picking same exercises more than once
            .first()  # get the first item in the queryset
        )

        picked_exercises.append(picked_exercise)

    return picked_exercises
