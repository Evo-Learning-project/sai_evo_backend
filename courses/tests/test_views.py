from courses.logic import privileges
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
    UserCoursePrivilege,
)
from django.test import TestCase
from rest_framework.test import APIClient, force_authenticate
from users.models import User


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher1 = User.objects.create(username="teacher1", is_teacher=True)
        self.student1 = User.objects.create(username="student1", is_teacher=False)
        self.teacher2 = User.objects.create(username="teacher2", is_teacher=True)
        self.student2 = User.objects.create(username="student2", is_teacher=False)


class CourseViewSetTestCase(BaseTestCase):
    def test_course_CRUD(self):
        course_name = "test_course"
        course_post_body = {"name": course_name}

        # show a teacher can create courses
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.post("/courses/", course_post_body)

        self.assertEquals(response.status_code, 201)
        self.assertEquals(Course.objects.count(), 1)

        self.assertEqual(response.data["name"], course_name)
        course_pk = response.data["id"]

        response = self.client.get(f"/courses/{course_pk}/")
        self.assertEquals(response.status_code, 200)

        self.assertEquals(Course.objects.count(), 1)
        self.assertEquals(Course.objects.get(pk=course_pk).creator, self.teacher1)

        # show a non-teacher user cannot create courses
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/courses/", {"name": "not gonna happen"})

        self.assertEquals(response.status_code, 403)
        self.assertEquals(Course.objects.count(), 1)

        # show a course creator can update their course
        new_course_name = "test_course_1"
        course_put_body = {"name": new_course_name}

        self.client.force_authenticate(user=self.teacher1)
        response = self.client.put(f"/courses/{course_pk}/", course_put_body)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(Course.objects.count(), 1)

        self.assertEqual(response.data["name"], new_course_name)
        self.assertEqual(course_pk, response.data["id"])

        # show a user without `update_course` permission cannot update that course
        newer_course_name = "test_course_2"
        course_put_body = {"name": newer_course_name}

        self.client.force_authenticate(user=self.teacher2)
        response = self.client.put(f"/courses/{course_pk}/", course_put_body)

        self.assertEquals(response.status_code, 403)

        # show a user with `update_course` permission can update that course
        UserCoursePrivilege.objects.create(
            user=self.teacher2,
            course=Course.objects.get(pk=course_pk),
            allow_privileges=[privileges.UPDATE_COURSE],
        )

        response = self.client.put(f"/courses/{course_pk}/", course_put_body)
        self.assertEqual(response.data["name"], newer_course_name)

        self.assertEquals(response.status_code, 200)

        # show nobody can delete courses
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(f"/courses/{course_pk}/")
        self.assertEquals(response.status_code, 403)
        self.client.force_authenticate(user=self.teacher2)
        response = self.client.delete(f"/courses/{course_pk}/")
        self.assertEquals(response.status_code, 403)
        self.assertEquals(Course.objects.count(), 1)
        response = self.client.get(f"/courses/{course_pk}/")
        self.assertEquals(response.status_code, 200)


class ExerciseViewSetTestCase(BaseTestCase):
    def test_exercise_CRUD(self):
        course_pk = Course.objects.create(name="test1", creator=self.teacher1).pk

        # show the course creator can CRUD exercises and their
        # choices/test cases/sub-exercises
        exercise_text = "abc"
        choice1 = {"text": "c1", "score": "-1.0"}
        choice2 = {"text": "c2", "score": "1.5"}
        choices = [choice1, choice2]
        exercise_post_body = {
            "text": exercise_text,
            "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            "choices": choices,
        }

        self.client.force_authenticate(user=self.teacher1)
        response = self.client.post(
            f"/courses/{course_pk}/exercises/", exercise_post_body
        )

        self.assertEquals(response.status_code, 201)
        self.assertEquals(
            Exercise.objects.filter(course_id=course_pk).count(),
            1,
        )

        self.assertEqual(response.data["text"], exercise_text)

        exercise_pk = response.data["id"]

        response = self.client.get(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 200)
        response = self.client.get(f"/courses/{course_pk}/exercises/")
        self.assertEquals(response.status_code, 200)

        # show a user without permissions cannot access the view at all
        self.client.force_authenticate(user=self.teacher2)
        response = self.client.get(f"/courses/{course_pk}/exercises/")
        self.assertEquals(response.status_code, 403)

        response = self.client.get(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 403)

        response = self.client.delete(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 403)

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.get(f"/courses/{course_pk}/exercises/2222/")
        self.assertEquals(response.status_code, 403)

        response = self.client.post(
            f"/courses/{course_pk}/exercises/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        self.client.force_authenticate(user=self.student1)
        response = self.client.get(f"/courses/{course_pk}/exercises/")
        self.assertEquals(response.status_code, 403)

        response = self.client.get(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 403)

        response = self.client.delete(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 403)

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.get(f"/courses/{course_pk}/exercises/2222/")
        self.assertEquals(response.status_code, 403)

        response = self.client.post(
            f"/courses/{course_pk}/exercises/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/"
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/1/"
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.post(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/",
            {
                "text": "not gonna happen either",
                "score": "1.00",
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.delete(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/1/"
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/1/",
            {
                "text": "not gonna happen either",
                "score": "1.00",
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/1/",
            {
                "text": "not gonna happen either",
                "score": "1.00",
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/"
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/1/"
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.post(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.delete(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/1/",
        )
        self.assertEquals(response.status_code, 403)

        # show a user with `create_exercises` permission can create exercises
        UserCoursePrivilege.objects.create(
            user=self.student1,
            course=Course.objects.get(pk=course_pk),
            allow_privileges=[
                privileges.CREATE_EXERCISES,
                privileges.ACCESS_EXERCISES,
                privileges.MODIFY_EXERCISES,
            ],
        )

        self.client.force_authenticate(user=self.student1)
        response = self.client.get(f"/courses/{course_pk}/exercises/")
        self.assertEquals(response.status_code, 200)

        response = self.client.get(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 200)

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "new text",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "newer text",
            },
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.delete(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 204)

        response = self.client.get(f"/courses/{course_pk}/exercises/2222/")
        self.assertEquals(response.status_code, 404)

        response = self.client.post(
            f"/courses/{course_pk}/exercises/",
            {
                "text": "one more exercise",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 201)
        exercise_pk = response.data["id"]

        response = self.client.get(f"/courses/{course_pk}/exercises/")
        self.assertEquals(response.status_code, 200)

        response = self.client.get(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 200)

        # response = self.client.delete(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        # self.assertEquals(response.status_code, 204)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/"
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.post(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/",
            {
                "text": "new choice",
                "score": "1.00",
            },
        )
        self.assertEquals(response.status_code, 201)
        choice_pk = response.data["id"]

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/{choice_pk}/",
            {
                "text": "new choice text",
                "score": "21.00",
            },
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/{choice_pk}/",
            {
                "text": "newer choice text",
            },
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/{choice_pk}/"
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.delete(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/{choice_pk}/"
        )
        self.assertEquals(response.status_code, 204)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/"
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.get(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/22/"
        )
        self.assertEquals(response.status_code, 404)

        response = self.client.post(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/",
            {
                "text": "new sub-exercise",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 201)
        sub_exercise_pk = response.data["id"]

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/{sub_exercise_pk}/",
            {
                "text": "new subex text",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/{sub_exercise_pk}/",
            {
                "text": "newer subext text",
            },
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.delete(
            f"/courses/{course_pk}/exercises/{exercise_pk}/sub_exercises/{sub_exercise_pk}/",
        )
        self.assertEquals(response.status_code, 204)

    def test_view_queryset(self):
        # show that, for each course, you can only access that course's
        # exercises from the course's endpoint
        pass


class EventViewSetTestCase(BaseTestCase):
    def test_exercise_create_update_delete(self):
        # show the course creator can create and update events

        # show a non-teacher user cannot create or update events

        # show a user with `create_events` permission can create events

        # show a user with `update_events` permission can update events

        # show a user without `create_events` permission cannot create events

        # show a user without `update_events` permission cannot update events

        # show only the course creator can delete events

        pass

    def test_view_queryset(self):
        # show that, for each course, you can only access that course's
        # events from the course's endpoint
        pass


class EventParticipationViewSetTestCase(BaseTestCase):
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

    def test_view_queryset(self):
        # show that, for each event, you can only access that events's
        # participations from the events's endpoint
        pass
