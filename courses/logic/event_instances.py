from random import shuffle
from courses.models import EventTemplate, Exercise


def get_exercises_from(
    template: EventTemplate, public_only=False, exclude_seen_in_practice=False
):
    """
    Returns a list of pair (exercise, rule) where rule is a rule of the given template
    and exercise is an exercise picked using the rule's criteria

    Args:
        template (EventTemplate): the template to use for retrieving exercises
        public_only (bool, optional): whether only exercises with state equal to
        PUBLIC should be retrieved. Defaults to False.
        exclude_seen_in_practice (bool, optional): whether exercises that
        the user has seen in at least one SELF_SERVICE_PRACTICE Event
        should be disqualified from being picked. Defaults to False.

    Returns:
        List[(Exercise, EventTemplateRule)]: a list of pairs representing the picked
        exercises and the rules they were picked according to
    """
    course = template.event.course
    exercises = Exercise.objects.base_exercises().filter(
        course=course
    )  # TODO prefetch?

    if public_only:
        exercises = exercises.public()

    if False and exclude_seen_in_practice:  # ! temporarily disable feature
        exercises = exercises.not_seen_in_practice_by(template.event.creator)

    picked_exercises = []
    rules = template.rules.all()

    for rule in rules:
        rule_qs = exercises.satisfying(rule)

        rule_picked_exercises = rule_qs.exclude(
            pk__in=[e.pk for e, _ in picked_exercises]  # don't pick same exercise again
        ).get_random(amount=rule.amount)

        for picked_exercise in rule_picked_exercises:
            picked_exercises.append((picked_exercise, rule))

    if template.event.randomize_rule_order:
        shuffle(picked_exercises)

    return picked_exercises
