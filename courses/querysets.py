import random

from django.db import models
from django.db.models import aggregates
from django.db.models.aggregates import Max, Min


class ExerciseQuerySet(models.QuerySet):
    def base_exercises(self):
        """
        Returns the exercises that don't have a parent foreign key
        (i.e. that aren't a sub-exercise)
        """
        return self.filter(parent__isnull=True)

    def satisfying(self, rule):
        """
        Returns the exercises that satisfy an EventTemplateRule
        """
        from courses.models import EventTemplateRule

        if rule.rule_type == EventTemplateRule.ID_BASED:
            ret_qs = self.filter(pk__in=[e.pk for e in rule.exercises.all()])
        else:  # tag-based rule
            ret_qs = self
            for clause in rule.clauses.all():
                ret_qs = ret_qs.filter(tags__in=[t for t in clause.tags.all()])
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
        picked_ids = random.sample(ids, amount)

        ret = qs.filter(pk__in=picked_ids)
        return ret.first() if amount == 1 else ret

    def get_random_with_priority(self, priority_field, amount=1, exclude=None):
        """
        Returns `amount` random exercise(s) from the queryset, the
        chance of each exercise being picked depending on the value of
        `priority_field` - lower values (positive) have higher priority probability
        """
        pass


class SlotModelQuerySet(models.QuerySet):
    def base_slots(self):
        """
        Returns the slots that don't have a parent foreign key
        (i.e. that aren't a sub-slot)
        """
        return self.filter(parent__isnull=True)
