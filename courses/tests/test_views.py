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


class CourseViewSetTestCase(TestCase):
    def setUp(self):
        pass

    def test_course_CRUD(self):
        # show a teacher can create courses

        # show a non-teacher user cannot create courses

        # show a course creator can update their course
        # show a user with `update_course` permission can update that course
        # show a user without `update_course` permission cannot update that course

        # show nobody can delete courses
        pass


class ExerciseViewSetTestCase(TestCase):
    def setUp(self):
        pass

    def test_exercise_CRUD(self):
        # show the course creator can CRUD exercises and their choices

        # show a non-teacher user cannot access the view at all

        # show a user with `access_exercises` permission can list/retrieve exercises
        # and their choices/test cases/sub-exercises

        # show a user without `modify_exercises` permission can update/delete exercises
        # and their choices/test cases/sub-exercises

        pass


class EventViewSetTestCase(TestCase):
    def setUp(self):
        pass

    def test_exercise_create_update_delete(self):
        # show the course creator can create and update events

        # show a non-teacher user cannot create or update events

        # show a user with `create_events` permission can create events

        # show a user with `update_events` permission can update events

        # show a user without `create_events` permission cannot create events

        # show a user without `update_events` permission cannot update events

        # show only the course creator can delete events

        pass


class EventParticipationViewSetTestCase(TestCase):
    def setUp(self):
        pass

    def test_participation_submission_and_assessment(self):
        # show an allowed user can create a participation

        # show the appropriate serializer is displayed to the user

        # show a user that's not the owner of the participation cannot retrieve or
        # update it and its slots

        # show participations cannot be deleted by anyone

        # show the owner of the participation can update the participation's slots

        # show that only the submission related fields can be updated

        # show that the owner of a participation can turn it in

        # show that after it's been turned in, no fields or slots can be updated

        # show a user with `access_participations` permission can see the participation(s)
        # show the appropriate serializer is being used

        # show a user with `assess_participations` permission can update the assessment
        # related fields (and only those)

        # show a user with `access_participations` or `assess_participations` cannot
        # create a participation of their own

        pass
