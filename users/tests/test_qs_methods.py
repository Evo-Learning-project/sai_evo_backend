from courses.models import (
    Course,
    Event,
    EventParticipation,
    Exercise,
)
from django.test import TestCase
from users.models import User


class UserQsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="a", email="aaa@bbb.com")
        self.user2 = User.objects.create(username="b", email="aab@bbb.com")
        self.user3 = User.objects.create(username="c", email="aac@bbb.com")
        self.course = Course.objects.create(name="course")
        self.event_exam1 = Event.objects.create(
            name="event", event_type=Event.EXAM, course=self.course
        )
        self.event_exam2 = Event.objects.create(
            name="event2", event_type=Event.EXAM, course=self.course
        )
        self.event_practice = Event.objects.create(
            name="event3",
            event_type=Event.SELF_SERVICE_PRACTICE,
            course=self.course,
            creator=self.user2,
        )

    def test_active_users(self):
        self.assertListEqual(
            [],
            [u for u in User.objects.all().active_in_course(course_id=self.course.pk)],
        )

        EventParticipation.objects.create(user=self.user1, event_id=self.event_exam1.pk)
        self.assertListEqual(
            [self.user1],
            [u for u in User.objects.all().active_in_course(course_id=self.course.pk)],
        )
        EventParticipation.objects.create(user=self.user1, event_id=self.event_exam2.pk)
        self.assertListEqual(
            [self.user1],
            [u for u in User.objects.all().active_in_course(course_id=self.course.pk)],
        )

        EventParticipation.objects.create(
            user=self.user2, event_id=self.event_practice.pk
        )
        self.assertListEqual(
            [self.user1, self.user2],
            [u for u in User.objects.all().active_in_course(course_id=self.course.pk)],
        )
