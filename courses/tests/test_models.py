from decimal import Decimal
from time import time
from django.forms import ValidationError

from courses.tests.data import courses

from django.utils import timezone

from courses.models import (
    Course,
    Event,
    EventParticipation,
    Exercise,
    ExerciseChoice,
)
from django.test import TestCase
from users.models import User


def common_setup(self):
    self.user = User.objects.create(email="aaa@bbb.com")
    self.course = Course.objects.create(name="course")
    self.event_exam = Event.objects.create(
        name="event", event_type=Event.EXAM, course=self.course
    )

    self.e_multiple_single_choices = [
        {
            "text": "aa",
            "correctness": "1",
        },
        {
            "text": "bb",
            "correctness": "0.5",
        },
        {
            "text": "cc",
            "correctness": "-0.2",
        },
    ]
    self.e_multiple_single = Exercise.objects.create(
        text="a",
        course=self.course,
        exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
        choices=self.e_multiple_single_choices,
    )

    self.e_multiple_multiple_choices = [
        {
            "text": "aa",
            "correctness": "1",
        },
        {
            "text": "bb",
            "correctness": "-0.5",
        },
        {
            "text": "cc",
            "correctness": "0.5",
        },
    ]
    self.e_multiple_multiple = Exercise.objects.create(
        text="b",
        course=self.course,
        exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
        choices=self.e_multiple_multiple_choices,
    )
    self.e_open = Exercise.objects.create(
        text="c",
        course=self.course,
        exercise_type=Exercise.OPEN_ANSWER,
    )
    self.e_aggregated = Exercise.objects.create(
        text="c",
        course=self.course,
        exercise_type=Exercise.AGGREGATED,
        sub_exercises=[
            {
                "text": "aaa",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                "choices": [
                    {
                        "text": "a",
                    },
                    {
                        "text": "b",
                    },
                ],
            },
            {
                "text": "bbb",
                "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
                "choices": [
                    {
                        "text": "a",
                    },
                    {
                        "text": "b",
                    },
                ],
            },
        ],
    )
    self.e_completion = Exercise.objects.create(
        text="c",
        course=self.course,
        exercise_type=Exercise.COMPLETION,
        choices=[
            [
                {
                    "text": "1c1",
                },
                {
                    "text": "1c2",
                },
            ],
            [
                {
                    "text": "2c1",
                },
                {
                    "text": "2c2",
                },
            ],
            [
                {
                    "text": "3c1",
                },
                {
                    "text": "3c2",
                },
                {
                    "text": "3c3",
                },
            ],
        ],
    )
    self.e_js = Exercise.objects.create(
        text="abc",
        course=self.course,
        exercise_type=Exercise.JS,
        testcases=[{"code": "assert true"}, {"code": "assert false"}],
    )

    # self.participation = EventParticipation(
    #     user=self.user,
    # )
    # self.participation.save()


class ModelPropertiesTestCase(TestCase):
    def setUp(self):
        common_setup(self)

    def test_courses(self):
        self.assertEqual(self.course.name, str(self.course))

    def test_exercises(self):
        pass
        # exercises' score
        # self.assertEqual(self.e_multiple_single.max_score, round(Decimal(1.00), 2))
        # self.assertEqual(self.e_multiple_multiple.max_score, round(Decimal(1.60), 2))
        # self.assertEqual(self.e_js.max_score, round(Decimal(2.00), 2))

        # correct choices
        # TODO update tests with new correctness logic
        # self.assertListEqual(
        #     [c.text for c in self.e_multiple_single.get_correct_choices()],
        #     [self.e_multiple_single_choices[0]["text"]],
        # )
        # self.assertListEqual(
        #     [c.text for c in self.e_multiple_multiple.get_correct_choices()],
        #     [
        #         self.e_multiple_multiple_choices[0]["text"],
        #         self.e_multiple_multiple_choices[2]["text"],
        #     ],
        # )

    def test_events(self):
        e1 = Event.objects.create(
            course=self.course, name="test_event_1", event_type=Event.DRAFT
        )

        e1.begin_timestamp = timezone.localtime(timezone.now())
        e1.state = Event.PLANNED
        e1.save()

        # event automatically begins at begin_time if PLANNED
        self.assertEqual(e1.state, Event.OPEN)

        with self.assertRaises(ValidationError):
            e1.access_rule_exceptions = {}
            e1.save()

        with self.assertRaises(ValidationError):
            e1.access_rule_exceptions = ["abc", True]
            e1.save()

    def test_participation_current_exercise_property(self):
        pass

    def test_assessment_state_property(self):
        pass


class ModelConstraintsTestCase(TestCase):
    # TODO test
    def test_event_participation_uniqueness(self):
        pass

    def test_event_participation_permissions(self):
        pass

    def test_submission_constraints(self):
        # selecting a choice that's not in the exercise, etc.
        pass

    def test_closed_event_restrictions(self):
        # cannot participate or modify submissions in closed events
        pass


class ModelMethodsTestCase(TestCase):
    def test_participation_move_forward_and_back_methods(self):
        pass

    def test_exercise_get_assessment_rule(self):
        pass


class AbstractModelsTestCase(TestCase):
    def test_orderable_model(self):
        course = Course.objects.create(**courses.course_1)
        exercise = Exercise.objects.create(
            course=course,
            text="a",
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
        )

        """
        Show that ordering is correctly incremented as
        objects are created
        """
        choice_0 = ExerciseChoice.objects.create(
            correctness=0, text="a", exercise=exercise
        )
        self.assertEqual(choice_0._ordering, 0)

        choice_1 = ExerciseChoice.objects.create(
            correctness=0, text="a", exercise=exercise
        )
        self.assertEqual(choice_1._ordering, 1)

        choice_2 = ExerciseChoice.objects.create(
            correctness=0, text="a", exercise=exercise
        )
        self.assertEqual(choice_2._ordering, 2)

        choice_3 = ExerciseChoice.objects.create(
            correctness=0, text="a", exercise=exercise
        )
        self.assertEqual(choice_3._ordering, 3)

        """
        Show swapping models
        """
        # simple case: move choice 3 to position 2
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 2
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_2.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 0)
        self.assertEqual(choice_1._ordering, 1)
        self.assertEqual(choice_2._ordering, 3)
        self.assertEqual(choice_3._ordering, 2)

        # simple case: move choice 3 back to position 3
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 3
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_2.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 0)
        self.assertEqual(choice_1._ordering, 1)
        self.assertEqual(choice_2._ordering, 2)
        self.assertEqual(choice_3._ordering, 3)

        # more complex case, move choice 3 to 0
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 0
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_2.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 1)
        self.assertEqual(choice_1._ordering, 2)
        self.assertEqual(choice_2._ordering, 3)
        self.assertEqual(choice_3._ordering, 0)

        # more complex case, move choice 3 to 2
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 2
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_2.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 0)
        self.assertEqual(choice_1._ordering, 1)
        self.assertEqual(choice_2._ordering, 3)
        self.assertEqual(choice_3._ordering, 2)

        # move choice 3 back to 3
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 3
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_2.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 0)
        self.assertEqual(choice_1._ordering, 1)
        self.assertEqual(choice_2._ordering, 2)
        self.assertEqual(choice_3._ordering, 3)

        """
        Delete one choice and show this still works
        """

        choice_2.delete()

        # move choice 3 to a position that's not the one the deleted choice had
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 0
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 1)
        self.assertEqual(choice_1._ordering, 3)
        self.assertEqual(choice_3._ordering, 0)

        # move choice 3 back to 3
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 3
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 0)
        self.assertEqual(choice_1._ordering, 1)
        self.assertEqual(choice_3._ordering, 3)

        # move choice 3 to the position of the deleted choice
        choice_3 = ExerciseChoice.objects.get(
            pk=choice_3.pk
        )  # re-fetch to trigger from_db
        choice_3._ordering = 2
        choice_3.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 0)
        self.assertEqual(choice_1._ordering, 1)
        self.assertEqual(choice_3._ordering, 2)

        # move choice 0 to position 2
        choice_0 = ExerciseChoice.objects.get(
            pk=choice_0.pk
        )  # re-fetch to trigger from_db
        choice_0._ordering = 2
        choice_0.save()

        choice_0.refresh_from_db()
        choice_1.refresh_from_db()
        choice_3.refresh_from_db()

        self.assertEqual(choice_0._ordering, 2)
        self.assertEqual(choice_1._ordering, 0)
        self.assertEqual(choice_3._ordering, 1)
