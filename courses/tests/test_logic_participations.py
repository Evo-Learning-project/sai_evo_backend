import time
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient, force_authenticate
from courses.logic.participations import get_effective_time_limit, is_time_up
from data import users, courses, exercises, events
from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventParticipationSlot,
    EventTemplateRule,
    Exercise,
    UserCoursePrivilege,
)
from users.models import User
from django.utils import timezone


class ParticipationLogicTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.teacher_1 = User.objects.create(**users.teacher_1)
        self.course = Course.objects.create(creator=self.teacher_1, **courses.course_1)

        self.student_1 = User.objects.create(**users.student_1)
        self.student_2 = User.objects.create(**users.student_2)

        self.exercise_1 = Exercise.objects.create(
            course=self.course, **exercises.mmc_priv_1
        )
        self.exercise_2 = Exercise.objects.create(
            course=self.course, **exercises.msc_priv_1
        )
        self.event: Event = Event.objects.create(
            course=self.course, creator=self.teacher_1, **events.exam_1_one_at_a_time
        )

        rule_1 = EventTemplateRule.objects.create(
            template=self.event.template, rule_type=EventTemplateRule.ID_BASED
        )
        rule_1.exercises.set([self.exercise_1])
        rule_2 = EventTemplateRule.objects.create(
            template=self.event.template, rule_type=EventTemplateRule.ID_BASED
        )
        rule_2.exercises.set([self.exercise_2])

        # open event
        self.event.state = Event.PLANNED
        self.event.begin_timestamp = timezone.localdate(timezone.now())

    def test_event_time_limit(self):
        # set time limit to event
        self.event.time_limit_rule = Event.TIME_LIMIT
        self.event.time_limit_seconds = 2
        self.event.save()

        """
        Test validation of time limit exceptions
        """
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = {}
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = ""
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = None
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = [{}]
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = [1]
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = [""]
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = [["a", None]]
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = [["a", 1, False]]
            self.event.save()
        with self.assertRaises(ValidationError):
            self.event.time_limit_exceptions = [[1, 1]]
            self.event.save()

        # add a time limit exception for student 2
        self.event.time_limit_exceptions = [[self.student_2.email, 3]]
        self.event.save()

        """
        Show the correct time limit is returned depending on whether
        the user has a time limit exception in place for them or not
        """
        # no exception in place - event time limit is applied
        self.assertEqual(
            get_effective_time_limit(event=self.event, user=self.student_1),
            self.event.time_limit_seconds,
        )
        # time limit in the exception is applied
        self.assertEqual(
            get_effective_time_limit(event=self.event, user=self.student_2),
            3,
        )

        # time limit is None if event doesn't have the time limit rule set
        self.event.time_limit_rule = Event.NO_TIME_LIMIT
        self.event.save()
        self.assertIsNone(
            get_effective_time_limit(event=self.event, user=self.student_1),
        )
        self.assertIsNone(
            get_effective_time_limit(event=self.event, user=self.student_2),
        )

        self.event.time_limit_rule = Event.TIME_LIMIT
        self.event.save()

        """
        Show the time limit is enforced upon participations
        """
        participation_student_1 = EventParticipation.objects.create(
            user=self.student_1, event_id=self.event.pk
        )
        participation_student_2 = EventParticipation.objects.create(
            user=self.student_2, event_id=self.event.pk
        )

        self.assertFalse(is_time_up(participation_student_1, grace_period=0))
        self.assertFalse(is_time_up(participation_student_2, grace_period=0))

        time.sleep(self.event.time_limit_seconds)

        # two seconds have passed and first participation has run out of time
        self.assertTrue(is_time_up(participation_student_1, grace_period=0))
        # this user has a 3-second limit, therefore their participation hasn't
        # yet run out of time
        self.assertFalse(is_time_up(participation_student_2, grace_period=0))

        time.sleep(1)

        self.assertTrue(is_time_up(participation_student_1, grace_period=0))
        self.assertTrue(is_time_up(participation_student_2, grace_period=0))

        # grace period extends the time limit
        self.assertFalse(is_time_up(participation_student_1, grace_period=2))
        self.assertFalse(is_time_up(participation_student_2, grace_period=1))
