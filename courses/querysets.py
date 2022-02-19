import random

from django.db import models
from django.db.models import Q, aggregates
from django.db.models.aggregates import Max, Min


class ExerciseQuerySet(models.QuerySet):
    def base_exercises(self):
        """
        Returns the exercises that don't have a parent foreign key
        (i.e. that aren't a sub-exercise)
        """
        return self.filter(parent__isnull=True)

    def draft(self):
        from courses.models import Exercise

        return self.filter(state=Exercise.DRAFT)

    def private(self):
        from courses.models import Exercise

        return self.filter(state=Exercise.PRIVATE)

    def public(self):
        from courses.models import Exercise

        return self.filter(state=Exercise.PUBLIC)

    def satisfying(self, rule):
        """
        Returns the exercises that satisfy an EventTemplateRule
        """
        from courses.models import EventTemplateRule

        ret_qs = self

        if rule.rule_type == EventTemplateRule.ID_BASED:
            ret_qs = ret_qs.filter(pk__in=[e.pk for e in rule.exercises.all()])
        elif rule.rule_type == EventTemplateRule.TAG_BASED:
            for clause in rule.clauses.all():
                clause_tags = clause.tags.all()
                # TODO test
                qs_filter = Q(public_tags__in=clause_tags)
                if not rule.search_public_tags_only:
                    qs_filter |= Q(private_tags__in=clause_tags)

                ret_qs = ret_qs.filter(qs_filter)
            ret_qs = (
                ret_qs.distinct()
            )  # if more than one tag match, an item may be returned more than once

        return ret_qs

    def get_random(self, amount=1):
        """
        Returns `amount` random exercise(s) from the queryset
        """
        qs = self

        ids = list(qs.values_list("pk", flat=True))

        # avoid trying to pick a larger sample than the list of id's
        amount = min(amount, len(ids))

        picked_ids = random.sample(
            ids,
            amount,
        )

        ret = qs.filter(pk__in=picked_ids)
        return ret


class SlotModelQuerySet(models.QuerySet):
    def base_slots(self):
        """
        Returns the slots that don't have a parent foreign key
        (i.e. that aren't a sub-slot)
        """
        return self.filter(parent__isnull=True)


class EventTemplateQuerySet(models.QuerySet):
    def public(self):
        """
        Returns the slots that don't have a parent foreign key
        (i.e. that aren't a sub-slot)
        """
        return self.filter(public=True)
