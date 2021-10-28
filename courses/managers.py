from django.db import models
from django.db.models import Q

# class ExerciseQuerySet(models.QuerySet):
#     def from_template(self, template):
#         from .models import Exercise

#         exercises = Exercise.objects.all()
#         condition = Q()
#         for rule in template.rules.all():
#             rule_qs = exercises
#             for clause in rule.clauses.all():


# class ExerciseManager(models.Manager):
#     def get_queryset(self):
#         return ExerciseQuerySet(self.model, using=self._db)

#     def from_template(self, template):
#         return self.get_queryset.from_template(template=template)


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
