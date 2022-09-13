from random import shuffle
from typing import List
from courses.models import EventTemplate, EventTemplateRule, Exercise
from django.db.models import Q
import random


def prefetch_exercises_from_rules(
    initial_qs, rules: List[EventTemplateRule]
) -> List[Exercise]:
    """
    Eagerly fetch all exercises related to the list of rules passed. This
    limits the number of queries and allows to work in memory with the exercises
    """
    condition = Q()
    for rule in rules:
        if rule.rule_type == EventTemplateRule.ID_BASED:
            condition |= Q(pk__in=rule.exercises.all().values("pk"))

    ret = [e for e in initial_qs.filter(condition).with_prefetched_related_objects()]
    return ret


def get_random_exercises_from_list(
    exercises: List[Exercise], amount: int
) -> List[Exercise]:
    ids = [e.pk for e in exercises]

    # avoid trying to pick a larger sample than the list of id's
    amount = min(amount, len(ids))

    picked_ids = random.sample(
        ids,
        amount,
    )
    return [e for e in exercises if e.pk in picked_ids]


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
    rules: List[EventTemplateRule] = [
        r for r in template.rules.all().prefetch_related("exercises")
    ]
    prefetched_exercises = prefetch_exercises_from_rules(exercises, rules)

    for rule in rules:
        # TODO extract to separate method (possibly create a class to handle the whole flow)
        if rule.rule_type == EventTemplateRule.ID_BASED:
            # use prefetched exercises to limit db hits
            rule_ids = [e.pk for e in rule.exercises.all()]
            rule_picked_exercises = get_random_exercises_from_list(
                [e for e in prefetched_exercises if e.pk in rule_ids],
                rule.amount,
            )
        else:
            rule_qs = exercises.satisfying(rule)
            rule_picked_exercises = rule_qs.exclude(
                pk__in=[
                    e.pk for e, _ in picked_exercises
                ]  # don't pick same exercise again
            ).get_random(amount=rule.amount)

        for picked_exercise in rule_picked_exercises:
            picked_exercises.append((picked_exercise, rule))

    if template.event.randomize_rule_order:
        shuffle(picked_exercises)

    return picked_exercises
