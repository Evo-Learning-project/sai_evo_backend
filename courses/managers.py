from django.db import models
from django.db.models import Q


class ExerciseManager(models.Manager):
    def create(self, *args, **kwargs):
        """
        Creates a new exercise and the correct related entities (choices,
        test cases) depending on the exercise type
        """
        from .models import Exercise, ExerciseChoice, ExerciseTestCase

        choices = kwargs.pop("choices", [])
        testcases = kwargs.pop("testcases", [])
        exercise = super().create(*args, **kwargs)

        if exercise.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE:
            # create ExerciseChoice objects related to this exercise
            for choice in choices:
                ExerciseChoice.objects.create(exercise=exercise, **choice)
        elif exercise.exercise_type == Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE:
            for choice in choices:
                # create a sub-exercise with no text and a single choice for
                # each of the choices supplied
                Exercise.objects.create(
                    parent=exercise,
                    exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                    choices=[choice],
                )
        elif exercise.exercise_type == Exercise.COMPLETION:
            # for each list of choices in `choices`, create a related
            # sub-exercise with no text and those choices
            for choice_group in choices:
                Exercise.objects.create(
                    parent=exercise,
                    exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                    choices=choice_group,
                )
        elif exercise.exercise_type == Exercise.JS:
            # create ExerciseTestcase objects related to this exercise
            for testcase in testcases:
                ExerciseTestCase.objects.create(exercise=exercise, **testcase)
        elif exercise.exercise_type == Exercise.AGGREGATED:
            # create sub-exercises related to this exercise
            for sub_exercise in kwargs.get("sub_exercises"):
                Exercise.objects.create(parent=exercise, **sub_exercise)

        return exercise


class EventParticipationManager(models.Manager):
    def create(self, event=None, event_instance=None, *args, **kwargs):
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

        if event_instance is None and event is None:
            raise ValueError("Either provide an Event or an EventInstance")

        if event_instance is None:
            event_instance = EventInstance.objects.create(event=event)

        kwargs["event_instance"] = event_instance
        participation = super().create(*args, **kwargs)

        ParticipationSubmission.objects.create(participation=participation)
        ParticipationAssessment.objects.create(participation=participation)

        return participation


class EventInstanceManager(models.Manager):
    def create(self, *args, **kwargs):
        """
        Creates an event instance. A list of exercises can be supplied to have the instance contain
        those exercises. If no such list is supplied, the exercises are chosen applying the rules
        in the event template
        """
        from .logic.event_instances import get_exercises_from
        from .models import EventInstanceSlot

        instance = super().create(*args, **kwargs)
        event_template = kwargs["event"].template

        if (exercises := kwargs.get("exercises")) is None:
            exercises = get_exercises_from(event_template)

        slot_number = 0
        for exercise in exercises:
            EventInstanceSlot.objects.create(
                event_instance=instance,
                exercise=exercise,
                slot_number=slot_number,
            )
            slot_number += 1

        return instance


class ParticipationSubmissionManager(models.Manager):
    def create(self, *args, **kwargs):
        from .models import ParticipationSubmissionSlot

        submission = super().create(*args, **kwargs)

        for slot in submission.participation.event_instance.slots.all():
            ParticipationSubmissionSlot.objects.create(
                submission=submission, slot_number=slot.slot_number
            )

        return submission


class ParticipationAssessmentManager(models.Manager):
    def create(self, *args, **kwargs):
        from .models import ParticipationAssessmentSlot

        assessment = super().create(*args, **kwargs)

        for slot in assessment.participation.event_instance.slots.all():
            ParticipationAssessmentSlot.objects.create(
                assessment=assessment, slot_number=slot.slot_number
            )

        return assessment
