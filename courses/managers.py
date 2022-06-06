from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from courses.querysets import (
    CourseQuerySet,
    EventParticipationQuerySet,
    ExerciseQuerySet,
    SlotModelQuerySet,
    TagQuerySet,
)

from django.utils import timezone


class CourseManager(models.Manager):
    def get_queryset(self):
        return CourseQuerySet(self.model, using=self._db)

    def public(self):
        return self.get_queryset().public()


class TagManager(models.Manager):
    def get_queryset(self):
        return TagQuerySet(self.model, using=self._db)

    def public(self):
        return self.get_queryset().public()


class ExerciseManager(models.Manager):
    def get_queryset(self):
        return ExerciseQuerySet(self.model, using=self._db)

    def base_exercises(self):
        return self.get_queryset().base_exercises()

    def draft(self):
        return self.get_queryset().draft()

    def private(self):
        return self.get_queryset().private()

    def public(self):
        return self.get_queryset().public()

    def create(self, *args, **kwargs):
        """
        Creates a new exercise and the correct related entities (choices,
        test cases) depending on the exercise type
        """
        from .models import Exercise, ExerciseChoice, ExerciseTestCase

        choices = kwargs.pop("choices", [])
        testcases = kwargs.pop("testcases", [])
        sub_exercises = kwargs.pop("sub_exercises", [])

        # if kwargs.get("parent") is not None or kwargs.get("parent_id") is not None:
        #     parent = kwargs.get("parent") or Exercise.objects.get(
        #         pk=kwargs["parent_id"]
        #     )
        #     kwargs["child_position"] = parent.get_next_child_position()

        exercise = super().create(*args, **kwargs)

        # TODO review everything
        if (
            exercise.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE
            or exercise.exercise_type == Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE
            or exercise.exercise_type == Exercise.OPEN_ANSWER
            or exercise.exercise_type == Exercise.COMPLETION
            or exercise.exercise_type == Exercise.AGGREGATED
            or exercise.exercise_type == Exercise.ATTACHMENT
        ) and len(testcases) > 0:
            raise ValidationError("Non-JS exercises cannot have test cases")

        if (
            exercise.exercise_type == Exercise.OPEN_ANSWER
            or exercise.exercise_type == Exercise.JS
            or exercise.exercise_type == Exercise.C
            or exercise.exercise_type == Exercise.AGGREGATED
            or exercise.exercise_type == Exercise.ATTACHMENT
        ) and len(choices) > 0:
            raise ValidationError(
                "Open answer, attachment, aggregated, and coding exercises cannot have choices"
            )

        if (
            exercise.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE
            or exercise.exercise_type == Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE
        ):
            for choice in choices:
                ExerciseChoice.objects.create(exercise=exercise, **choice)

        elif exercise.exercise_type == Exercise.COMPLETION:
            child_position = 0
            # for each list of choices in `choices`, create a related
            # sub-exercise with no text and those choices
            for choice_group in choices:
                Exercise.objects.create(
                    parent=exercise,
                    course=exercise.course,
                    exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                    choices=choice_group,
                    # child_position=child_position,
                )
                child_position += 1
        elif (
            exercise.exercise_type == Exercise.JS
            or exercise.exercise_type == Exercise.C
        ):
            # create ExerciseTestcase objects related to this exercise
            for testcase in testcases:
                ExerciseTestCase.objects.create(exercise=exercise, **testcase)
        elif exercise.exercise_type == Exercise.AGGREGATED:
            child_position = 0
            # create sub-exercises related to this exercise
            for sub_exercise in sub_exercises:
                Exercise.objects.create(
                    parent=exercise,
                    course=exercise.course,
                    # child_position=child_position,
                    **sub_exercise,
                )
                child_position += 1

        return exercise


class EventParticipationManager(models.Manager):
    def get_queryset(self):
        return EventParticipationQuerySet(self.model, using=self._db)

    def create(self, *args, **kwargs):
        """
        Creates an event participation and its related slots
        """
        from .logic.event_instances import get_exercises_from
        from .models import EventParticipationSlot, Event

        assert (
            kwargs["event_id"] is not None
        )  # TODO eventually remove this when you make event field non-nullable

        participation = super().create(*args, **kwargs)

        if (exercises := kwargs.pop("exercises", None)) is None:
            event = Event.objects.get(pk=kwargs["event_id"])
            event_template = event.template

            # use event template to get a list of exercises for this participation
            exercises = get_exercises_from(
                event_template,
                public_only=(event.event_type == Event.SELF_SERVICE_PRACTICE),
                exclude_seen_in_practice=(
                    event.event_type == Event.SELF_SERVICE_PRACTICE
                ),
            )

        slot_number = 0
        for exercise in exercises:
            now = timezone.localtime(timezone.now())
            # mark first slot as seen
            seen_at_kwarg = {"seen_at": now} if slot_number == 0 else {}

            EventParticipationSlot.objects.create(
                participation=participation,
                exercise=exercise,
                slot_number=slot_number,
                **seen_at_kwarg,
            )
            slot_number += 1

        return participation


class EventParticipationSlotManager(models.Manager):
    def get_queryset(self):
        return SlotModelQuerySet(self.model, using=self._db)

    def base_slots(self):
        return self.get_queryset().base_slots()

    def create(self, *args, **kwargs):
        from .models import EventParticipationSlot

        slot = super().create(*args, **kwargs)

        sub_slot_number = 0
        # recursively create slots that reference sub-exercises
        for sub_exercise in slot.exercise.sub_exercises.all():
            EventParticipationSlot.objects.create(
                parent=slot,
                participation=slot.participation,
                exercise=sub_exercise,
                slot_number=sub_slot_number,
            )
            sub_slot_number += 1

        return slot


class EventManager(models.Manager):
    def create(self, *args, **kwargs):
        from .models import EventTemplate

        event = super().create(*args, **kwargs)

        # automatically create an event template for this event
        event.template = EventTemplate.objects.create(course=event.course)
        event.save()

        return event


class EventTemplateRuleManager(models.Manager):
    def create(self, *args, **kwargs):
        """
        Creates an EventTemplateRule.

        If the rule is ID-based, expects to receive an iterable of Exercise
        If the rule is tag-based, expects to receive a list of iterables of Tag
        """
        from .models import EventTemplateRule, EventTemplateRuleClause

        tags = kwargs.pop("tags", [])
        exercises = kwargs.pop("exercises", [])

        rule = super().create(*args, **kwargs)

        if rule.rule_type == EventTemplateRule.ID_BASED:
            if len(tags) > 0:
                raise ValidationError("ID-based rules cannot have tag clauses")
            for exercise in exercises:
                if exercise.parent is not None:
                    raise ValidationError(
                        "You can only directly assign base exercises to an EventRule"
                    )
            rule.exercises.set(exercises)
        elif rule.rule_type == EventTemplateRule.TAG_BASED:
            if len(exercises) > 0:
                raise ValidationError(
                    "Tag-based rules cannot refer to specific exercises"
                )
            for tag_group in tags:
                clause = EventTemplateRuleClause.objects.create(rule=rule)
                clause.tags.set(tag_group)
        else:  # fully random rule
            if len(tags) > 0 or len(exercises) > 0:
                raise ValidationError(
                    "Fully random rules cannot have tag clauses or specify exercises"
                )

        return rule
