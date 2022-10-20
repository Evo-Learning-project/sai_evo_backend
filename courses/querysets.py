import random
import string

from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Max, Min, Count
from django.db.models import Prefetch
from django.db.models import Sum, Case, When, Value


from .logic.privileges import ACCESS_EXERCISES, MANAGE_EXERCISES, get_user_privileges


from users.models import User
from content.models import VoteModel

from django.db.models import Exists, OuterRef


class ExerciseQuerySet(models.QuerySet):
    def with_solutions_bookmarked_by(self, user: User):
        from .models import ExerciseSolution

        bookmarked_solution_exists_query = (
            ExerciseSolution.objects.all()
            .bookmarked_by(user)
            .filter(
                exercise=OuterRef("pk"),
            )
        )
        return self.annotate(
            bookmarked_solution_exists=Exists(bookmarked_solution_exists_query)
        ).filter(bookmarked_solution_exists=True)

    def with_solutions_visible_by(self, course_id: str, user: User):
        """Returns the exercises from course with id course_id for which
        user is allowed to access the solutions.

        If user has ACCESS_EXERCISES or MANAGE_EXERCISES privileges over the course, all
        exercises are visible to them.

        Otherwise, only exercises with visibility PUBLIC or exercises that are included
        in at least one EventParticipationSlot whose EventParticipation either belongs
        to a SELF_SERVICE_PRACTICE Event or has its assessment published are visible

        Args:
            course_id: Course to which restrict the queryset
            user (User): User for whom to check permissions
        """
        from .models import Exercise, EventParticipationSlot, EventParticipation, Event

        # !!
        privileges = get_user_privileges(user, course_id)

        if ACCESS_EXERCISES in privileges or MANAGE_EXERCISES in privileges:
            return self

        eligible_slot_exists_subquery = EventParticipationSlot.objects.filter(
            Q(participation___assessment_state=EventParticipation.PUBLISHED)
            | Q(participation__event__event_type=Event.SELF_SERVICE_PRACTICE),
            participation__event__course_id=course_id,
            participation__user=user,
            exercise=OuterRef("pk"),
        )

        return self.annotate(
            eligible_slot_exists=Exists(eligible_slot_exists_subquery)
        ).filter(Q(eligible_slot_exists=True) | Q(state=Exercise.PUBLIC))

    def visible_by(self, course_id: str, user: User):
        from .models import Exercise, EventParticipationSlot, EventParticipation, Event

        # !!
        privileges = get_user_privileges(user, course_id)

        if ACCESS_EXERCISES in privileges or MANAGE_EXERCISES in privileges:
            return self

        eligible_slot_exists_subquery = EventParticipationSlot.objects.filter(
            participation__event__course_id=course_id,
            participation__user=user,
            # TODO verify that slot is in scope
            exercise=OuterRef("pk"),
        )

        return self.annotate(
            eligible_slot_exists=Exists(eligible_slot_exists_subquery)
        ).filter(Q(eligible_slot_exists=True) | Q(state=Exercise.PUBLIC))

    def order_by_popularity(self):
        return self.annotate(solution_count=Count("solutions")).order_by(
            "-solution_count"
        )

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

    def with_submitted_solutions(self):
        from .models import ExerciseSolution

        exists_submitted_solution_subquery = ExerciseSolution.objects.all().filter(
            state=ExerciseSolution.SUBMITTED, exercise=OuterRef("pk")
        )
        return self.annotate(
            submitted_solution_exists=Exists(exists_submitted_solution_subquery)
        ).filter(submitted_solution_exists=True)

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

        if rule.rule_type is None:
            # if rule type is unset, return empty queryset
            return Exercise.objects.none()

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

    def with_prefetched_related_objects(self):
        return self.prefetch_related(
            "private_tags",
            "public_tags",
            "choices",
            "testcases",
            "sub_exercises",
            "sub_exercises__choices",
            "sub_exercises__testcases",
            "sub_exercises__private_tags",
            "sub_exercises__public_tags",
            "sub_exercises__sub_exercises",
        )

    def get_random(self, amount=1):
        """
        Returns `amount` random exercise(s) from the queryset
        """
        return self.order_by("?")[:amount]
        # qs = self

        # ids = list(qs.values_list("pk", flat=True))

        # # avoid trying to pick a larger sample than the list of id's
        # amount = min(amount, len(ids))

        # picked_ids = random.sample(
        #     ids,
        #     amount,
        # )

        # ret = qs.filter(pk__in=picked_ids)
        # return ret


class ExerciseSolutionQuerySet(models.QuerySet):
    def with_prefetched_related_objects(self):
        return self.select_related("_content", "user").prefetch_related(
            "votes",
            "comments",
            "bookmarked_by",
        )

    def bookmarked_by(self, user):
        return self.filter(bookmarked_by__in=[user])

    def exclude_draft_and_rejected(self):
        from courses.models import ExerciseSolution

        return self.exclude(
            (Q(state=ExerciseSolution.REJECTED) | Q(state=ExerciseSolution.DRAFT))
        )

    def exclude_draft_and_rejected_unless_authored_by(self, user):
        from courses.models import ExerciseSolution

        return self.exclude(
            (Q(state=ExerciseSolution.REJECTED) | Q(state=ExerciseSolution.DRAFT))
            & ~Q(user=user)
        )

    def exclude_draft_unless_authored_by(self, user):
        from courses.models import ExerciseSolution

        return self.exclude(Q(state=ExerciseSolution.DRAFT) & ~Q(user=user))

    def order_by_published_first(self):
        from courses.models import ExerciseSolution

        return self.annotate(
            state_value=Case(
                When(state=ExerciseSolution.PUBLISHED, then=Value(2)),
                When(state=ExerciseSolution.SUBMITTED, then=Value(1)),
                default=Value(0),
                output_field=models.PositiveSmallIntegerField(),
            ),
        ).order_by("-state_value")

    def order_by_score_descending(self):
        return self.annotate(
            votes_score=Sum(
                Case(
                    When(votes__vote_type=VoteModel.DOWN_VOTE, then=Value(-1)),
                    When(votes__vote_type=VoteModel.UP_VOTE, then=Value(1)),
                    default=Value(0),
                    output_field=models.SmallIntegerField(),
                ),
                default=0,
            )
        ).order_by("-votes_score")

    def with_prefetched_exercise_and_related_objects(self):
        return self.select_related("exercise").prefetch_related(
            "exercise__private_tags",
            "exercise__public_tags",
            "exercise__choices",
            "exercise__testcases",
            "exercise__sub_exercises",
            "exercise__sub_exercises__choices",
            "exercise__sub_exercises__testcases",
            "exercise__sub_exercises__private_tags",
            "exercise__sub_exercises__public_tags",
            "exercise__sub_exercises__sub_exercises",
        )


class EventParticipationQuerySet(models.QuerySet):
    def with_prefetched_base_slots(self):
        from courses.models import EventParticipationSlot

        return self.prefetch_related(
            Prefetch(
                "slots",
                queryset=EventParticipationSlot.objects.base_slots()
                .select_related("exercise", "populating_rule")
                .prefetch_related(
                    "sub_slots",
                    "selected_choices",
                    "exercise__choices",
                    "exercise__testcases",
                    "exercise__sub_exercises",
                    "exercise__sub_exercises__choices",
                    "exercise__sub_exercises__testcases",
                    "exercise__sub_exercises__private_tags",
                    "exercise__sub_exercises__public_tags",
                    "exercise__sub_exercises__sub_exercises",
                    "exercise__public_tags",
                    "exercise__private_tags",
                )
                .annotate(
                    prefetched_max_choice_correctness=Max(
                        "exercise__choices__correctness"
                    )
                ),
                to_attr="prefetched_base_slots",
            )
        )

    def annotate_with_max_score_correctness(self):
        return self.annotate(max_choice_correctness=Max("choices__correctness"))


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
        from courses.models import Exercise

        return self.annotate(
            public_in_public_exercise_count=Count(
                "public_in_exercises",
                filter=Q(public_in_exercises__state=Exercise.PUBLIC),
            )
        ).filter(public_in_public_exercise_count__gt=0)
