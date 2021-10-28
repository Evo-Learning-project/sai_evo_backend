from courses.models import EventTemplateRule, Exercise


def get_exercises_from(template, pool=None):
    exercises = Exercise.objects.all()
    if pool is not None:
        exercises = exercises.filter(pk__in=pool)

    picked_ids = []
    for rule in template.rules.all():
        if rule.rule_type == EventTemplateRule.ID_BASED:
            rule_qs = exercises.filter(pk__in=[e.pk for e in rule.exercises.all()])
        else:  # tag-based rule
            rule_qs = exercises
            for clause in rule.clauses.all():
                rule_qs = rule_qs.filter(tags__in=[t for t in clause.tags.all()])

    picked_id = (
        rule_qs.distict()  # if more than one tag match, an item may be returned more than once
        .order_by("?")  # shuffle entries
        .values("id")  # only retrive id's for better performance
        .exclude(pk__in=picked_ids)  # avoid picking same id's more than once
        .first()  # get the first item in the queryset
    )
    picked_ids.append(picked_id)

    return Exercise.objects.filter(pk__in=picked_ids)
