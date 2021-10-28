from courses.models import EventTemplateRule, Exercise


def get_exercises_from(template, pool=None):
    exercises = Exercise.objects.all()
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
        rule_qs.distict()  # if more than one tag match, an item may be returned more than once
        .order_by("?")  # shuffle entries
        .exclude(pk__in=picked_exercises)  # avoid picking same id's more than once
        .first()  # get the first item in the queryset
    )
    picked_exercises.append(picked_exercise)

    # if this exercise has sub_exercises, add them to the list of picked exercises too
    for sub_exercise in picked_exercise.sub_exercises.all():
        picked_exercises.append(sub_exercise)

    return picked_exercises
