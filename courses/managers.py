from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from courses.querysets import EventTemplateQuerySet, ExerciseQuerySet, SlotModelQuerySet


class SlottedModelManager(models.Manager):
    def create_sub_slots_for(self, from_slot, parent):
        """
        Recursively creates slots (with given parent) associated to the
        sub-slots of `from_slot`
        """

        # name of the argument containing foreign key to parent and its value
        related_object_kwarg = {
            self.model._meta.verbose_name.split(" ")[1]: getattr(
                parent, self.model._meta.verbose_name.split(" ")[1]
            )
        }

        slot_model = type(parent)

        for sub_slot in from_slot.sub_slots.all():
            new_slot = slot_model.objects.create(
                parent=parent,
                slot_number=sub_slot.slot_number,
                **related_object_kwarg,
            )
            self.create_sub_slots_for(sub_slot, new_slot)

    def create(self, *args, **kwargs):
        from django.apps import apps

        obj = super().create(*args, **kwargs)

        # name of the argument containing foreign key to parent and its value
        related_object_kwarg = {self.model._meta.verbose_name.split(" ")[1]: obj}

        slot_model = apps.get_model(f"courses.{self.model.__name__}Slot")

        for slot in obj.participation.event_instance.slots.base_slots():
            # create a related slot for each base slot in the related EventInstance
            new_slot = slot_model.objects.create(
                slot_number=slot.slot_number,
                parent=None,
                **related_object_kwarg,
            )
            self.create_sub_slots_for(slot, new_slot)

        return obj


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
            or exercise.exercise_type == Exercise.AGGREGATED
            or exercise.exercise_type == Exercise.ATTACHMENT
        ) and len(choices) > 0:
            raise ValidationError(
                "Open answer, attachment, aggregated, and JS exercises cannot have choices"
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
                    child_position=child_position,
                )
                child_position += 1
        elif exercise.exercise_type == Exercise.JS:
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
                    child_position=child_position,
                    **sub_exercise,
                )
                child_position += 1

        return exercise


class EventParticipationManager(models.Manager):
    def create(self, event_id=None, event_instance=None, *args, **kwargs):
        """
        Creates an event participation. If supplied an EventInstance, assigns that instance
        to the new participation, otherwise creates one on demand and assigns it to the new
        participation. If no EventInstance is supplied, an Event argument must be supplied
        """
        from .models import (
            EventInstance,
            ParticipationAssessment,
            ParticipationSubmission,
        )

        if event_instance is None and event_id is None:
            raise ValueError("Either provide an Event or an EventInstance")

        if event_instance is None:
            event_instance = EventInstance.objects.create(event_id=event_id)

        kwargs["event_instance_id"] = event_instance.pk
        participation = super().create(*args, **kwargs)

        ParticipationSubmission.objects.create(participation=participation)
        ParticipationAssessment.objects.create(participation=participation)

        participation.save()

        return participation


class EventInstanceManager(models.Manager):
    def create(self, *args, **kwargs):
        """
        Creates an event instance. A list of exercises can be supplied to have the instance contain
        those exercises. If no such list is supplied, the exercises are chosen applying the rules
        in the event template
        """
        from .logic.event_instances import get_exercises_from
        from .models import Event, EventInstanceSlot

        if (exercises := kwargs.pop("exercises", None)) is None:
            event = Event.objects.get(pk=kwargs["event_id"])
            event_template = event.template

            exercises = get_exercises_from(
                event_template,
                public_only=(event.event_type == Event.SELF_SERVICE_PRACTICE),
            )

        instance = super().create(*args, **kwargs)

        slot_number = 0
        for exercise in exercises:
            EventInstanceSlot.objects.create(
                event_instance=instance,
                exercise=exercise,
                slot_number=slot_number,
            )
            slot_number += 1

        return instance


class EventInstanceSlotManager(models.Manager):
    def get_queryset(self):
        return SlotModelQuerySet(self.model, using=self._db)

    def base_slots(self):
        return self.get_queryset().base_slots()

    def create(self, *args, **kwargs):
        from .models import EventInstanceSlot

        slot = super().create(*args, **kwargs)

        sub_slot_number = 0
        # recursively create slots that reference sub-exercises
        for sub_exercise in slot.exercise.sub_exercises.all():
            EventInstanceSlot.objects.create(
                parent=slot,
                event_instance=slot.event_instance,
                exercise=sub_exercise,
                slot_number=sub_slot_number,
            )
            sub_slot_number += 1

        return slot


class ParticipationSubmissionSlotManager(models.Manager):
    def get_queryset(self):
        return SlotModelQuerySet(self.model, using=self._db)

    def base_slots(self):
        return self.get_queryset().base_slots()


class ParticipationAssessmentSlotManager(models.Manager):
    def get_queryset(self):
        return SlotModelQuerySet(self.model, using=self._db)

    def base_slots(self):
        return self.get_queryset().base_slots()


class ParticipationSubmissionManager(SlottedModelManager):
    pass


class ParticipationAssessmentManager(SlottedModelManager):
    pass


class EventManager(models.Manager):
    def create(self, *args, **kwargs):
        from .models import EventTemplate

        event = super().create(*args, **kwargs)

        # automatically create an event template for this event
        event.template = EventTemplate.objects.create(course=event.course)
        event.save()

        return event


class EventTemplateManager(models.Manager):
    def get_queryset(self):
        return EventTemplateQuerySet(self.model, using=self._db)

    def public(self):
        return self.get_queryset().public()

    def create(self, *args, **kwargs):
        from .models import EventTemplateRule

        # rules = kwargs.pop("rules", [])
        template = super().create(*args, **kwargs)

        # target_slot_number = 0
        # for rule in rules:
        #     EventTemplateRule.objects.create(
        #         template=template,
        #         target_slot_number=target_slot_number,
        #         **rule,
        #     )
        #     target_slot_number += 1

        return template


class EventTemplateRuleManager(models.Manager):
    def create(self, *args, **kwargs):
        # from .models import EventTemplate

        # kwargs["target_slot_number"] = EventTemplate.objects.get(
        #     pk=kwargs["template_id"]
        # ).get_next_rule_target_slot_number()
        return super().create(*args, **kwargs)

    # def create(self, *args, **kwargs):
    #     """
    #     Creates an EventTemplateRule.

    #     If the rule is ID-based, expects to receive an iterable of Exercise
    #     If the rule is tag-based, expectes to receive a list of iterables of Tag
    #     """
    #     from .models import EventTemplateRule, EventTemplateRuleClause

    #     tags = kwargs.pop("tags", [])
    #     exercises = kwargs.pop("exercises", [])

    #     rule = super().create(*args, **kwargs)

    #     if rule.rule_type == EventTemplateRule.ID_BASED:
    #         if len(tags) > 0:
    #             raise ValidationError("ID-based rules cannot have tag clauses")
    #         for exercise in exercises:
    #             if exercise.parent is not None:
    #                  TODO this should be kept around
    #                 raise ValidationError(
    #                     "You can only directly assign base exercises to an EventRule"
    #                 )
    #         rule.exercises.set(exercises)
    #     elif rule.rule_type == EventTemplateRule.TAG_BASED:
    #         if len(exercises) > 0:
    #             raise ValidationError(
    #                 "Tag-based rules cannot refer to specific exercises"
    #             )
    #         for tag_group in tags:
    #             clause = EventTemplateRuleClause.objects.create(rule=rule)
    #             clause.tags.set(tag_group)
    #     else:  # fully random rule
    #         if len(tags) > 0 or len(exercises) > 0:
    #             raise ValidationError(
    #                 "Fully random rules cannot have tag clauses or specify exercises"
    #             )

    #     return rule
