from courses.models import Exercise


def get_exercises_from(template, public_only=False, exclude_seen_in_practice=False):
    course = template.event.course
    exercises = Exercise.objects.base_exercises().filter(
        course=course
    )  # TODO prefetch?

    if public_only:
        exercises = exercises.public()

    if False and exclude_seen_in_practice:
        exercises = exercises.not_seen_in_practice_by(template.event.creator)

    picked_exercises = []
    rules = template.rules.all()
    if template.event.randomize_rule_order:
        rules = rules.order_by("?")

    for rule in rules:
        rule_qs = exercises.satisfying(rule)

        rule_picked_exercises = rule_qs.exclude(
            pk__in=[e.pk for e in picked_exercises]  # don't pick same exercise again
        ).get_random(amount=rule.amount)
        picked_exercises.extend(rule_picked_exercises)

    return picked_exercises
