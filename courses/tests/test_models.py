from courses.models import (
    Course,
    Event,
    EventInstance,
    EventInstanceSlot,
    EventParticipation,
    Exercise,
    ParticipationAssessment,
    ParticipationAssessmentSlot,
    ParticipationSubmission,
    ParticipationSubmissionSlot,
)
from django.test import TestCase
from users.models import User


def common_setup(self):
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

    event_instance = EventInstance(event=self.event_exam)
    event_instance.save()

    # slots for event_instance
    self.instance_slot_0 = EventInstanceSlot(
        event_instance=event_instance,
        slot_number=0,
        exercise=self.e_multiple_single,
    )
    self.instance_slot_0.save()
    self.instance_slot_1 = EventInstanceSlot(
        event_instance=event_instance,
        slot_number=1,
        exercise=self.e_multiple_multiple,
    )
    self.instance_slot_1.save()
    self.instance_slot_2 = EventInstanceSlot(
        event_instance=event_instance,
        slot_number=2,
        exercise=self.e_open,
    )
    self.instance_slot_2.save()

    # sub-slots of slot_1
    self.instance_slot_1_0 = EventInstanceSlot(
        event_instance=event_instance,
        slot_number=0,
        parent=self.instance_slot_1,
        exercise=self.e_multiple_multiple.sub_exercises.all()[0],
    )
    self.instance_slot_1_0.save()
    self.instance_slot_1_1 = EventInstanceSlot(
        event_instance=event_instance,
        slot_number=1,
        parent=self.instance_slot_1,
        exercise=self.e_multiple_multiple.sub_exercises.all()[1],
    )
    self.instance_slot_1_1.save()
    self.instance_slot_1_2 = EventInstanceSlot(
        event_instance=event_instance,
        slot_number=2,
        parent=self.instance_slot_1,
        exercise=self.e_multiple_multiple.sub_exercises.all()[2],
    )
    self.instance_slot_1_2.save()

    self.participation = EventParticipation(
        event_instance=event_instance,
        user=self.user,
    )
    self.participation.save()

    participation_submission = ParticipationSubmission(participation=self.participation)
    participation_submission.save()
    self.participation.save()

    # slots for participation_submission
    self.submission_slot_0 = ParticipationSubmissionSlot(
        submission=participation_submission,
        slot_number=0,
    )
    self.submission_slot_0.save()
    self.submission_slot_1 = ParticipationSubmissionSlot(
        submission=participation_submission,
        slot_number=1,
    )
    self.submission_slot_1.save()
    self.submission_slot_2 = ParticipationSubmissionSlot(
        submission=participation_submission,
        slot_number=2,
    )
    self.submission_slot_2.save()

    # sub-slots of slot_1
    self.submission_slot_1_0 = ParticipationSubmissionSlot(
        submission=participation_submission,
        slot_number=0,
        parent=self.submission_slot_1,
    )
    self.submission_slot_1_0.save()
    self.submission_slot_1_1 = ParticipationSubmissionSlot(
        submission=participation_submission,
        slot_number=1,
        parent=self.submission_slot_1,
    )
    self.submission_slot_1_1.save()
    self.submission_slot_1_2 = ParticipationSubmissionSlot(
        submission=participation_submission,
        slot_number=2,
        parent=self.submission_slot_1,
    )
    self.submission_slot_1_2.save()

    participation_assessment = ParticipationAssessment(participation=self.participation)
    participation_assessment.save()
    self.participation.save()

    # slots for participation_assessment
    self.assessment_slot_0 = ParticipationAssessmentSlot(
        assessment=participation_assessment,
        slot_number=0,
    )
    self.assessment_slot_0.save()
    self.assessment_slot_1 = ParticipationAssessmentSlot(
        assessment=participation_assessment,
        slot_number=1,
    )
    self.assessment_slot_1.save()
    self.assessment_slot_2 = ParticipationAssessmentSlot(
        assessment=participation_assessment,
        slot_number=2,
    )
    self.assessment_slot_2.save()

    # sub-slots of slot_1
    self.assessment_slot_1_0 = ParticipationAssessmentSlot(
        assessment=participation_assessment,
        slot_number=0,
        parent=self.assessment_slot_1,
    )
    self.assessment_slot_1_0.save()
    self.assessment_slot_1_1 = ParticipationAssessmentSlot(
        assessment=participation_assessment,
        slot_number=1,
        parent=self.assessment_slot_1,
    )
    self.assessment_slot_1_1.save()
    self.assessment_slot_1_2 = ParticipationAssessmentSlot(
        assessment=participation_assessment,
        slot_number=2,
        parent=self.assessment_slot_1,
    )
    self.assessment_slot_1_2.save()


class ModelPropertiesTestCase(TestCase):
    def setUp(self):
        common_setup(self)

    def test_sibling_slot_access(self):
        self.assertEqual(self.assessment_slot_0.submission, self.submission_slot_0)
        self.assertEqual(self.assessment_slot_1.submission, self.submission_slot_1)
        self.assertEqual(self.assessment_slot_1_0.submission, self.submission_slot_1_0)
        self.assertEqual(self.assessment_slot_1_1.submission, self.submission_slot_1_1)
        self.assertEqual(self.assessment_slot_1_2.submission, self.submission_slot_1_2)
        self.assertEqual(self.assessment_slot_2.submission, self.submission_slot_2)

        self.assertEqual(self.submission_slot_0.assessment, self.assessment_slot_0)
        self.assertEqual(self.submission_slot_1.assessment, self.assessment_slot_1)
        self.assertEqual(self.submission_slot_1_0.assessment, self.assessment_slot_1_0)
        self.assertEqual(self.submission_slot_1_1.assessment, self.assessment_slot_1_1)
        self.assertEqual(self.submission_slot_1_2.assessment, self.assessment_slot_1_2)
        self.assertEqual(self.submission_slot_2.assessment, self.assessment_slot_2)

        self.assertEqual(
            self.instance_slot_0.get_submission(self.participation),
            self.submission_slot_0,
        )
        self.assertEqual(
            self.instance_slot_1.get_submission(self.participation),
            self.submission_slot_1,
        )
        self.assertEqual(
            self.instance_slot_1_0.get_submission(self.participation),
            self.submission_slot_1_0,
        )
        self.assertEqual(
            self.instance_slot_1_1.get_submission(self.participation),
            self.submission_slot_1_1,
        )
        self.assertEqual(
            self.instance_slot_1_2.get_submission(self.participation),
            self.submission_slot_1_2,
        )
        self.assertEqual(
            self.instance_slot_2.get_submission(self.participation),
            self.submission_slot_2,
        )

        self.assertEqual(
            self.instance_slot_0.get_assessment(self.participation),
            self.assessment_slot_0,
        )
        self.assertEqual(
            self.instance_slot_1.get_assessment(self.participation),
            self.assessment_slot_1,
        )
        self.assertEqual(
            self.instance_slot_1_0.get_assessment(self.participation),
            self.assessment_slot_1_0,
        )
        self.assertEqual(
            self.instance_slot_1_1.get_assessment(self.participation),
            self.assessment_slot_1_1,
        )
        self.assertEqual(
            self.instance_slot_1_2.get_assessment(self.participation),
            self.assessment_slot_1_2,
        )
        self.assertEqual(
            self.instance_slot_2.get_assessment(self.participation),
            self.assessment_slot_2,
        )

    def test_slot_exercise_property(self):
        self.assertEqual(
            self.instance_slot_0.exercise,
            self.submission_slot_0.exercise,
        )
        self.assertEqual(
            self.instance_slot_0.exercise,
            self.assessment_slot_0.exercise,
        )

        self.assertEqual(
            self.instance_slot_1.exercise,
            self.submission_slot_1.exercise,
        )
        self.assertEqual(
            self.instance_slot_1.exercise,
            self.assessment_slot_1.exercise,
        )

        self.assertEqual(
            self.instance_slot_1_0.exercise,
            self.submission_slot_1_0.exercise,
        )
        self.assertEqual(
            self.instance_slot_1_0.exercise,
            self.assessment_slot_1_0.exercise,
        )

        self.assertEqual(
            self.instance_slot_1_1.exercise,
            self.submission_slot_1_1.exercise,
        )
        self.assertEqual(
            self.instance_slot_1_1.exercise,
            self.assessment_slot_1_1.exercise,
        )

        self.assertEqual(
            self.instance_slot_1_2.exercise,
            self.submission_slot_1_2.exercise,
        )
        self.assertEqual(
            self.instance_slot_1_2.exercise,
            self.assessment_slot_1_2.exercise,
        )

        self.assertEqual(
            self.instance_slot_2.exercise,
            self.submission_slot_2.exercise,
        )
        self.assertEqual(
            self.instance_slot_2.exercise,
            self.assessment_slot_2.exercise,
        )

    def test_participation_current_exercise_property(self):
        pass

    def test_assessment_state_property(self):
        pass


class ModelConstraintsTestCase(TestCase):
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
