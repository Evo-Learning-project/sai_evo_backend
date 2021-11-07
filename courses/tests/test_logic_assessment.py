from courses.models import (
    Course,
    Event,
    EventInstance,
    EventParticipation,
    Exercise,
    ExerciseAssessmentRule,
    ParticipationAssessmentSlot,
)
from django.test import TestCase
from users.models import User


class SubmissionAssessorTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="aaa@bbb.com")
        self.course = Course.objects.create(name="course")
        self.event_exam = Event.objects.create(
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
                {"text": "bb", "correct": True},
                {"text": "cc", "correct": False},
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
            event=self.event_exam,
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
            event=self.event_exam,
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
        # setting `require_manual_assessment` disegards the rule parameters and returns None as score
        assessment_rule.require_manual_assessment = True
        assessment_rule.save()
        self.assertIsNone(e1_assessment.score)
        assessment_rule.require_manual_assessment = False
        assessment_rule.save()

        e1_submission.selected_choice = self.e_multiple_single.choices.filter(
            correct=True
        ).first()
        e1_submission.save()
        # rule for correct selected choice is applied
        self.assertEqual(e1_assessment.score, assessment_rule.points_for_correct)
        # setting `require_manual_assessment` disegards the rule parameters and returns None as score
        assessment_rule.require_manual_assessment = True
        assessment_rule.save()
        self.assertIsNone(e1_assessment.score)
        assessment_rule.require_manual_assessment = False
        assessment_rule.save()

        e1_submission.selected_choice = self.e_multiple_single.choices.filter(
            correct=False
        ).first()
        e1_submission.save()
        # rule for incorrect selected choice is applied
        self.assertEqual(e1_assessment.score, assessment_rule.points_for_incorrect)
        # setting `require_manual_assessment` disegards the rule parameters and returns None as score
        assessment_rule.require_manual_assessment = True
        assessment_rule.save()
        self.assertIsNone(e1_assessment.score)
        assessment_rule.require_manual_assessment = False
        assessment_rule.save()

        e1_assessment.score = 22
        e1_assessment.save()

        # manually setting the score overrides any assessment rules
        self.assertEqual(e1_assessment.score, 22)
        e1_submission.selected_choice = None
        e1_submission.save()
        self.assertEqual(e1_assessment.score, 22)
        e1_submission.selected_choice = self.e_multiple_single.choices.filter(
            correct=True
        ).first()
        e1_submission.save()
        self.assertEqual(e1_assessment.score, 22)
        e1_submission.selected_choice = self.e_multiple_single.choices.filter(
            correct=False
        ).first()
        e1_submission.save()
        self.assertEqual(e1_assessment.score, 22)
        # setting `require_manual_assessment` has no effect if there is a manual score assigned
        assessment_rule.require_manual_assessment = True
        assessment_rule.save()
        self.assertEqual(e1_assessment.score, 22)

    def test_assessment_multiple_choice_multiple_possible_exercise(self):
        assessment_rule = ExerciseAssessmentRule.objects.create(
            event=self.event_exam,
            exercise=self.e_multiple_multiple,
            points_for_correct=1,
            points_for_blank=0,
            points_for_incorrect=-0.5,
            minimum_score_threshold=2,
        )

        slots = self.participation.event_instance.slots.all()
        e2_slot = slots.get(exercise=self.e_multiple_multiple)
        e2_subslots = e2_slot.sub_slots.all()

        for subslot in e2_subslots:
            subslot_submission = subslot.get_submission(self.participation)
            subslot_assessment = subslot.get_assessment(self.participation)
            self.assertIsNone(subslot_submission.selected_choice)
            self.assertEqual(subslot_assessment.score, assessment_rule.points_for_blank)

        curr_subslot = e2_subslots[0]
        curr_submission = curr_subslot.get_submission(self.participation)
        curr_submission.selected_choice = curr_subslot.exercise.choices.first()
        curr_submission.save()
        curr_assessment = curr_subslot.get_assessment(self.participation)
        self.assertEqual(
            curr_assessment.score,
            assessment_rule.points_for_correct,  # first choice is correct
        )

        # score for the parent slot is still zero because the sum of the scores of the sub-slots
        # doesn't exceed the `minimum-score_threshold`
        self.assertEqual(e2_slot.get_assessment(self.participation).score, 0)

        curr_subslot = e2_subslots[1]
        curr_submission = curr_subslot.get_submission(self.participation)
        curr_submission.selected_choice = curr_subslot.exercise.choices.first()
        curr_submission.save()
        curr_assessment = curr_subslot.get_assessment(self.participation)
        self.assertEqual(
            curr_assessment.score,
            assessment_rule.points_for_correct,  # second choice is correct
        )

        # score for the parent slot finally exceeds `minimum_score_threshold`
        self.assertEqual(e2_slot.get_assessment(self.participation).score, 2)

        curr_subslot = e2_subslots[2]
        curr_submission = curr_subslot.get_submission(self.participation)
        curr_submission.selected_choice = curr_subslot.exercise.choices.first()
        curr_submission.save()
        curr_assessment = curr_subslot.get_assessment(self.participation)
        self.assertEqual(
            curr_assessment.score,
            assessment_rule.points_for_incorrect,  # second choice is incorrect
        )

        # score for the parent slot is 0 again because the sum of the scores of
        # the sub-exercises doesn't exceed `minimum_score_threshold` anymore
        self.assertEqual(e2_slot.get_assessment(self.participation).score, 0)

    def test_assessment_open_answer_exercise(self):
        slots = self.participation.event_instance.slots.all()
        e3_slot = slots.get(exercise=self.e_open)

        # open-answer exercises aren't assessed automatically in events of type EXAM
        self.assertIsNone(e3_slot.get_assessment(self.participation).score)
        self.assertEqual(
            e3_slot.get_assessment(self.participation).assessment_state,
            ParticipationAssessmentSlot.NOT_ASSESSED,
        )

        # open-answer exercises are assessed automatically in events of type
        # SELF_SERVICE_PRACTICE with score 0
        self.event_exam.event_type = Event.SELF_SERVICE_PRACTICE
        self.event_exam.save()
        self.assertEqual(e3_slot.get_assessment(self.participation).score, 0)
        self.assertEqual(
            e3_slot.get_assessment(self.participation).assessment_state,
            ParticipationAssessmentSlot.ASSESSED,
        )

        self.event_exam.event_type = Event.EXAM
        self.event_exam.save()

        # open-answer exercises can be assessed manually, resulting in
        # their score property being overridden
        e3_assessment = e3_slot.get_assessment(self.participation)
        self.assertEqual(
            e3_slot.get_assessment(self.participation).assessment_state,
            ParticipationAssessmentSlot.NOT_ASSESSED,
        )

        e3_assessment.score = 22
        e3_assessment.save()
        self.assertEqual(e3_slot.get_assessment(self.participation).score, 22)
        self.assertEqual(
            e3_slot.get_assessment(self.participation).assessment_state,
            ParticipationAssessmentSlot.ASSESSED,
        )
