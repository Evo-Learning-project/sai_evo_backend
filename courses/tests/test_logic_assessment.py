from courses.models import (
    Course,
    Event,
    EventInstance,
    EventParticipation,
    Exercise,
    ExerciseAssessmentRule,
)
from django.test import TestCase
from users.models import User


class SubmissionAssessorTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="aaa@bbb.com")
        self.course = Course.objects.create(name="course")
        self.event = Event.objects.create(
            name="event", event_type=Event.EXAM, course=self.course
        )
        self.e_multiple_single = Exercise.objects.create(
            text="a",
            course=self.course,
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            choices=[
                {"text": "aa", "correct": True},
                {"text": "bb", "correct": False},
                {"text": "cc", "correct": False},
            ],
        )
        self.e_multiple_multiple = Exercise.objects.create(
            text="b",
            course=self.course,
            exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            choices=[
                {"text": "aa", "correct": True},
                {"text": "bb", "correct": False},
                {"text": "cc", "correct": True},
                {"text": "dd", "correct": True},
                {"text": "ee", "correct": False},
            ],
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
                        {"text": "a", "correct": True},
                        {"text": "b", "correct": False},
                    ],
                },
                {
                    "text": "bbb",
                    "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
                    "choices": [
                        {"text": "a", "correct": True},
                        {"text": "b", "correct": False},
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
                    {"text": "1c1", "correct": True},
                    {"text": "1c2", "correct": False},
                ],
                [
                    {"text": "2c1", "correct": False},
                    {"text": "2c2", "correct": True},
                ],
                [
                    {"text": "3c1", "correct": False},
                    {"text": "3c2", "correct": True},
                    {"text": "3c3", "correct": False},
                ],
            ],
        )

        event_instance = EventInstance.objects.create(
            event=self.event,
            exercises=[
                self.e_multiple_single,
                self.e_multiple_multiple,
                self.e_open,
                self.e_aggregated,
                self.e_completion,
            ],
        )
        self.participation = EventParticipation.objects.create(
            event_instance=event_instance,
            user=self.user,
        )

    def test_assessment_multiple_choice_single_possible_exercise(self):
        assessment_rule = ExerciseAssessmentRule.objects.create(
            event=self.event,
            exercise=self.e_multiple_single,
            points_for_correct=1,
            points_for_blank=0.5,
            points_for_incorrect=-1,
        )

        slots = self.participation.event_instance.slots.all()
        e1_slot = slots.get(exercise=self.e_multiple_single)

        e1_submission = e1_slot.get_submission(self.participation)
        e1_assessment = e1_slot.get_assessment(self.participation)

        self.assertIsNone(e1_submission.selected_choice)
        # no choice was selected and the score wasn't,
        # overridden, therefore the score is `points_for_blank`
        self.assertEqual(e1_assessment.score, assessment_rule.points_for_blank)

        e1_submission.selected_choice = self.e_multiple_single.choices.filter(
            correct=True
        ).first()
        e1_submission.save()
        # rule for correct selected choice is applied
        self.assertEqual(e1_assessment.score, assessment_rule.points_for_correct)

        e1_submission.selected_choice = self.e_multiple_single.choices.filter(
            correct=False
        ).first()
        e1_submission.save()
        # rule for incorrect selected choice is applied
        self.assertEqual(e1_assessment.score, assessment_rule.points_for_incorrect)
