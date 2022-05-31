import random

from django.db import models
from django.db.models import Q, aggregates
from django.db.models.aggregates import Max, Min
from django.db.models import Prefetch


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

    def not_seen_in_practice_by(self, user):
        """
        Excludes exercises that have been seen by user in a practice
        """
        from .models import Event

        user_practice_participations = user.participations.filter(
            event__event_type=Event.SELF_SERVICE_PRACTICE
        )

        seen_exercises = user_practice_participations.values_list(
            "slots__exercise_id", flat=True
        )

        return self.exclude(pk__in=[e for e in seen_exercises if e is not None])

    def satisfying(self, rule):
        """
        Returns the exercises that satisfy an EventTemplateRule
        """
        from courses.models import EventTemplateRule, Exercise

        ret_qs = self.exclude(state=Exercise.DRAFT)

        if rule.rule_type == EventTemplateRule.ID_BASED:
            ret_qs = ret_qs.filter(pk__in=[e.pk for e in rule.exercises.all()])
        elif rule.rule_type == EventTemplateRule.TAG_BASED:
            for clause in rule.clauses.all():
                clause_tags = clause.tags.all()
                if not clause_tags.exists():  # empty clause
                    continue
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


class EventParticipationQuerySet(models.QuerySet):
    def with_prefetched_base_slots(self):
        from courses.models import EventParticipationSlot

        return self.prefetch_related(
            Prefetch(
                "slots",
                queryset=EventParticipationSlot.objects.base_slots()
                .select_related("exercise")
                .prefetch_related(
                    "sub_slots",
                    "selected_choices",
                    "exercise__choices",
                    "exercise__testcases",
                    "exercise__sub_exercises",
                    "exercise__public_tags",
                    "exercise__private_tags",
                ),
                to_attr="prefetched_base_slots",
            )
        )


class SlotModelQuerySet(models.QuerySet):
    def base_slots(self):
        """
        Returns the slots that don't have a parent foreign key
        (i.e. that aren't a sub-slot)
        """
        return self.filter(parent__isnull=True)


class CourseQuerySet(models.QuerySet):
    def public(self):
        return self.filter(hidden=False)


class TagQuerySet(models.QuerySet):
    def with_prefetched_public_exercises(self):
        from .models import Exercise

        return self.prefetch_related(
            Prefetch(
                "public_in_exercises",
                queryset=Exercise.objects.public(),
                to_attr="prefetched_public_in_public_exercises",
            ),
        )

    def with_prefetched_public_unseen_exercises(self, unseen_by):
        from .models import Exercise

        return self.prefetch_related(
            Prefetch(
                "public_in_exercises",
                queryset=Exercise.objects.public().not_seen_in_practice_by(unseen_by),
                to_attr="prefetched_public_in_unseen_public_exercises",
            )
        )

    def public(self):
        """
        A tag is public if it is in public_tags relationship with at least one public exercise
        """
        # TODO optimize
        qs = self.prefetch_related("public_in_exercises")
        pk_list = []

        for tag in qs:
            if (
                hasattr(tag, "prefetched_public_in_public_exercises")
                and len(tag.prefetched_public_in_public_exercises) > 0
                or tag.public_in_exercises.public().exists()
            ):
                pk_list.append(tag.pk)

        return qs.filter(id__in=pk_list)
