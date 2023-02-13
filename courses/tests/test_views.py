from decimal import Decimal
from time import sleep
from django.utils import timezone
from courses.logic import privileges
from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventParticipationSlot,
    EventTemplateRule,
    Exercise,
    ExerciseSolution,
    ExerciseSolutionVote,
    UserCourseEnrollment,
    UserCoursePrivilege,
)
from django.test import TestCase
from rest_framework.test import APIClient, force_authenticate
from users.models import User
from data import events


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

        UserCourseEnrollment.objects.create(user=self.student1, course_id=course_pk)

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
        UserCourseEnrollment.objects.create(user=self.student1, course_id=course_pk)

        """
        Show the course creator can CRUD exercises and their child models
        """
        exercise_text = "abc"
        choice1 = {"text": "c1", "correctness": "-0.7"}
        choice2 = {"text": "c2", "correctness": "1"}
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

        self.assertEquals(response.status_code, 200)  # TODO! fix this, it should be 201
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

        """
        Show a user without permissions cannot access the view in write mode
        """
        # as a teacher with no permissions on the course
        self.client.force_authenticate(user=self.teacher2)

        # creating exercises
        response = self.client.post(
            f"/courses/{course_pk}/exercises/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        # deleting exercises
        response = self.client.delete(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 403)

        # updating exercises
        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )

        # partially updating exercises
        self.assertEquals(response.status_code, 403)
        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
            },
        )
        self.assertEquals(response.status_code, 403)

        # response = self.client.get(f"/courses/{course_pk}/exercises/2222/")
        # self.assertEquals(response.status_code, 403)

        # as an unprivileged student
        self.client.force_authenticate(user=self.student1)

        # deleting exercises
        response = self.client.delete(f"/courses/{course_pk}/exercises/{exercise_pk}/")
        self.assertEquals(response.status_code, 403)

        # updating exercises
        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        # partially updating exercises
        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/",
            {
                "text": "not gonna happen",
            },
        )
        self.assertEquals(response.status_code, 403)

        # creating exercises
        response = self.client.post(
            f"/courses/{course_pk}/exercises/",
            {
                "text": "not gonna happen",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            },
        )
        self.assertEquals(response.status_code, 403)

        # CRUD on exercise children
        response = self.client.post(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/",
            {
                "text": "not gonna happen either",
                "score": "1.0",
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
                "score": "1.0",
            },
        )
        self.assertEquals(response.status_code, 403)

        response = self.client.patch(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/1/",
            {
                "text": "not gonna happen either",
                "score": "1.0",
            },
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

        # end CRUD on exercise children

        self.client.force_authenticate(user=self.student1)

        # show a user with `create_exercises` permission can create exercises
        UserCoursePrivilege.objects.create(
            user=self.student1,
            course=Course.objects.get(pk=course_pk),
            allow_privileges=[
                privileges.MANAGE_EXERCISES,
                privileges.ACCESS_EXERCISES,
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
        self.assertEquals(response.status_code, 200)  # todo! this should be 201
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
            {"text": "new choice", "correctness": "1"},
        )
        self.assertEquals(response.status_code, 201)
        choice_pk = response.data["id"]

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/{choice_pk}/",
            {
                "text": "new choice text",
                "correctness": "0.5",
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
        self.assertEquals(response.status_code, 200)  #! 201
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

    def test_exercise_access_policy(self):
        """
        Shows that, for a given course, unprivileged users can only access exercises
        that are either PUBLIC or that are included in a slot of a participation of
        the requesting user
        """
        from data.exercises import mmc_pub_1, mmc_priv_1, msc_priv_1, mmc_draft_1

        course = Course.objects.create(name="test_policy_course", creator=self.teacher1)
        UserCourseEnrollment.objects.create(user=self.student1, course=course)

        mmc_pub = Exercise.objects.create(course=course, **mmc_pub_1)
        mmc_priv = Exercise.objects.create(course=course, **mmc_priv_1)
        msc_priv = Exercise.objects.create(course=course, **msc_priv_1)
        mmc_draft = Exercise.objects.create(course=course, **mmc_draft_1)

        # unprivileged student
        self.client.force_authenticate(user=self.student1)

        """
        Shows that, in list view, only exercises that are either PUBLIC or that
        are included in a slot of a participation of the requesting user are
        shown in the response
        """
        response = self.client.get(f"/courses/{course.pk}/exercises/")
        self.assertEquals(response.status_code, 200)
        # response is paginated, access "results" to get the exercises
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn(mmc_pub.pk, [e["id"] for e in response.data["results"]])
        self.assertNotIn(mmc_priv.pk, [e["id"] for e in response.data["results"]])
        self.assertNotIn(msc_priv.pk, [e["id"] for e in response.data["results"]])
        self.assertNotIn(mmc_draft.pk, [e["id"] for e in response.data["results"]])

        mmc_priv.state = Exercise.PUBLIC
        mmc_priv.save()

        # mmc_priv has been made PUBLIC, so it's now included in the list response
        response = self.client.get(f"/courses/{course.pk}/exercises/")
        self.assertEquals(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIn(mmc_pub.pk, [e["id"] for e in response.data["results"]])
        self.assertIn(mmc_priv.pk, [e["id"] for e in response.data["results"]])
        self.assertNotIn(msc_priv.pk, [e["id"] for e in response.data["results"]])

        """
        Shows that accessing individual exercises works as long as they are
        accessible per the same criteria as above
        """
        response = self.client.get(f"/courses/{course.pk}/exercises/{mmc_pub.pk}/")
        self.assertEquals(response.status_code, 200)

        response = self.client.get(f"/courses/{course.pk}/exercises/{msc_priv.pk}/")
        self.assertEquals(response.status_code, 404)

        response = self.client.get(f"/courses/{course.pk}/exercises/{mmc_priv.pk}/")
        self.assertEquals(response.status_code, 200)

        response = self.client.get(f"/courses/{course.pk}/exercises/{mmc_draft.pk}/")
        self.assertEquals(response.status_code, 404)

        mmc_priv.state = Exercise.PRIVATE
        mmc_priv.save()

        response = self.client.get(f"/courses/{course.pk}/exercises/{mmc_priv.pk}/")
        self.assertEquals(response.status_code, 404)

        """
        Shows that, if an exercise is included in an EventParticipationSlot of
        an EventParticipation of the requesting user, it is accessible even
        when not PUBLIC
        """
        event = Event.objects.create(
            course=course, name="test_event", event_type=Event.EXAM
        )
        rule = EventTemplateRule.objects.create(
            template=event.template, rule_type=EventTemplateRule.ID_BASED
        )
        rule.exercises.set([msc_priv])

        # with no active participation with a slot that references it, exercise
        # isn't visible
        response = self.client.get(f"/courses/{course.pk}/exercises/{msc_priv.pk}/")
        self.assertEquals(response.status_code, 404)

        EventParticipation.objects.create(user=self.student1, event_id=event.pk)

        self.assertTrue(
            EventParticipationSlot.objects.filter(
                participation__user=self.student1, exercise=msc_priv
            ).exists()
        )

        # since it's included in a slot of the user, it's now visible
        response = self.client.get(f"/courses/{course.pk}/exercises/{msc_priv.pk}/")
        self.assertEquals(response.status_code, 200)


class ExerciseSolutionViewSetTestCase(BaseTestCase):
    def test_crud_solutions(self):
        """
        Shows that unprivileged users can only access solutions of exercises that:
        1. are visible to them
        2.1 are either PUBLIC, or
        2.2 are included in an EventParticipationSlot of an EventParticipation of the
        requesting user which either:
        2.2.1 is to an Event of event_type SELF_SERVICE_PRACTICE or
        2.2.2 which has its assessment_visibility set to PUBLISHED
        """
        from data.exercises import mmc_pub_1, mmc_priv_1, msc_priv_1, mmc_draft_1

        course = Course.objects.create(
            name="test_solution_policy_course", creator=self.teacher1
        )
        UserCourseEnrollment.objects.create(user=self.student1, course=course)

        mmc_pub = Exercise.objects.create(course=course, **mmc_pub_1)
        mmc_priv = Exercise.objects.create(course=course, **mmc_priv_1)
        msc_priv = Exercise.objects.create(course=course, **msc_priv_1)
        mmc_draft = Exercise.objects.create(course=course, **mmc_draft_1)

        # create solutions for exercises
        mmc_pub_sol_1 = ExerciseSolution.objects.create(
            user=self.teacher1,
            content="solution1",
            exercise=mmc_pub,
            state=ExerciseSolution.PUBLISHED,
        )
        mmc_priv_sol_1 = ExerciseSolution.objects.create(
            user=self.teacher1,
            content="solution2",
            exercise=mmc_priv,
            state=ExerciseSolution.PUBLISHED,
        )

        # unprivileged student
        self.client.force_authenticate(user=self.student1)

        # can access a PUBLIC exercise's solutions
        response = self.client.get(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/",
        )
        self.assertEquals(response.status_code, 200)

        # cannot access a PRIVATE exercise's solution which doesn't meet
        # the above criteria
        response = self.client.get(
            f"/courses/{course.pk}/exercises/{mmc_priv.pk}/solutions/",
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.get(
            f"/courses/{course.pk}/exercises/{mmc_priv.pk}/solutions/{mmc_priv_sol_1}/",
        )
        self.assertEquals(response.status_code, 403)

        # create an event participation for the user with mmc_priv in one of the slots
        event = Event.objects.create(
            course=course, name="test_event", event_type=Event.EXAM
        )
        rule = EventTemplateRule.objects.create(
            template=event.template, rule_type=EventTemplateRule.ID_BASED
        )
        rule.exercises.set([mmc_priv])
        participation = EventParticipation.objects.create(
            event_id=event.pk, user=self.student1
        )
        self.assertTrue(
            EventParticipationSlot.objects.filter(
                participation__user=self.student1, exercise=mmc_priv
            ).exists()
        )

        # still cannot access the solutions as the assessment isn't PUBLISHED
        response = self.client.get(
            f"/courses/{course.pk}/exercises/{mmc_priv.pk}/solutions/",
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.get(
            f"/courses/{course.pk}/exercises/{mmc_priv.pk}/solutions/{mmc_priv_sol_1}/",
        )
        self.assertEquals(response.status_code, 403)

        participation.assessment_visibility = EventParticipation.PUBLISHED
        participation.save()

        # assessment for the participation is PUBLISHED; solutions are now visible
        response = self.client.get(
            f"/courses/{course.pk}/exercises/{mmc_priv.pk}/solutions/",
        )
        self.assertEquals(response.status_code, 200)
        response = self.client.get(
            f"/courses/{course.pk}/exercises/{mmc_priv.pk}/solutions/{mmc_priv_sol_1.pk}/",
        )
        self.assertEquals(response.status_code, 200)

        """
        Shows that users can create ExerciseSolutions for exercises whose solutions
        are accessible to them
        """
        course = Course.objects.create(
            name="test_solution_policy_course_2", creator=self.teacher1
        )
        UserCourseEnrollment.objects.create(user=self.student1, course=course)

        mmc_pub = Exercise.objects.create(course=course, **mmc_pub_1)
        mmc_priv = Exercise.objects.create(course=course, **mmc_priv_1)
        msc_priv = Exercise.objects.create(course=course, **msc_priv_1)
        mmc_draft = Exercise.objects.create(course=course, **mmc_draft_1)

        # unprivileged student
        self.client.force_authenticate(user=self.student1)

        # cannot create solutions for exercises whose solutions aren't visible
        response = self.client.post(
            f"/courses/{course.pk}/exercises/{mmc_priv.pk}/solutions/",
            {"content": "abc"},
        )
        self.assertEquals(response.status_code, 403)

        # if exercise's solutions are visible, creating them is allowed
        response = self.client.post(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/",
            {"content": "abc"},
        )
        self.assertEquals(response.status_code, 201)
        solution_1_pk = response.data["id"]

        response = self.client.post(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/",
            {"content": "abc", "state": ExerciseSolution.SUBMITTED},
        )
        self.assertEquals(response.status_code, 201)

        # unprivileged users cannot create solutions in states other than DRAFT or SUBMITTED
        response = self.client.post(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/",
            {"content": "abc", "state": ExerciseSolution.PUBLISHED},
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.post(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/",
            {"content": "abc", "state": ExerciseSolution.REJECTED},
        )
        self.assertEquals(response.status_code, 403)

        # a user can update their solutions
        response = self.client.patch(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_1_pk}/",
            {"content": "abcd", "state": ExerciseSolution.SUBMITTED},
        )
        self.assertEquals(response.status_code, 200)

        # an unprivileged user cannot update their solution to be PUBLISHED or REJECTED
        response = self.client.patch(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_1_pk}/",
            {"state": ExerciseSolution.PUBLISHED},
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.patch(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_1_pk}/",
            {"state": ExerciseSolution.REJECTED},
        )
        self.assertEquals(response.status_code, 403)

        solution_2_pk = ExerciseSolution.objects.create(
            content="abcabc",
            exercise=mmc_pub,
            user=self.student2,
            state=ExerciseSolution.SUBMITTED,
        ).pk

        # an unprivileged user cannot update or delete somebody else's solutions
        response = self.client.patch(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_2_pk}/",
            {"content": "abc"},
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.put(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_2_pk}/",
            {"content": "abc", "state": ExerciseSolution.DRAFT},
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.delete(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_2_pk}/",
        )
        self.assertEquals(response.status_code, 403)

        """
        Shows that users can vote others' solutions and there can only be
        at most one vote per solution per user
        """
        self.assertEqual(
            ExerciseSolution.objects.get(pk=solution_2_pk)
            .votes.filter(user=self.student1)
            .count(),
            0,
        )
        response = self.client.put(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_2_pk}/vote/",
            {"vote_type": ExerciseSolutionVote.UP_VOTE},
        )
        self.assertEquals(response.status_code, 200)

        # first time a user votes, an ExerciseSolutionVote is created
        self.assertEqual(
            ExerciseSolution.objects.get(pk=solution_2_pk)
            .votes.filter(user=self.student1)
            .count(),
            1,
        )

        response = self.client.put(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_2_pk}/vote/",
            {"vote_type": ExerciseSolutionVote.DOWN_VOTE},
        )
        self.assertEquals(response.status_code, 200)

        # if same user votes again, the existing vote is updated and no new votes are created
        self.assertEqual(
            ExerciseSolution.objects.get(pk=solution_2_pk)
            .votes.filter(user=self.student1)
            .count(),
            1,
        )

        response = self.client.delete(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_2_pk}/vote/",
        )
        self.assertEquals(response.status_code, 200)

        # vote is deleted
        self.assertEqual(
            ExerciseSolution.objects.get(pk=solution_2_pk)
            .votes.filter(user=self.student1)
            .count(),
            0,
        )

        # a user cannot vote their own solutions
        response = self.client.put(
            f"/courses/{course.pk}/exercises/{mmc_pub.pk}/solutions/{solution_1_pk}/vote/",
            {"vote_type": ExerciseSolutionVote.UP_VOTE},
        )
        self.assertEquals(response.status_code, 403)


class EventViewSetTestCase(BaseTestCase):
    def test_exercise_create_update_delete(self):
        course = Course.objects.create(name="course", creator=self.teacher1)
        course_pk = course.pk

        UserCourseEnrollment.objects.create(user=self.student1, course=course)
        UserCourseEnrollment.objects.create(user=self.student2, course=course)

        # Show an unprivileged user cannot access the list of events of a course,
        # nor retrieve an event which is in draft state
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(
            f"/courses/{course_pk}/events/",
        )
        self.assertEquals(response.status_code, 403)

        draft_event_pk = Event.objects.create(
            **{**events.exam_1_all_at_once, "state": Event.DRAFT}, course=course
        ).pk
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(
            f"/courses/{course_pk}/events/{draft_event_pk}/",
        )
        self.assertEquals(response.status_code, 404)

        # Show the course creator can create and update events
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.post(
            f"/courses/{course_pk}/events/",
            {**events.exam_1_all_at_once, "state": Event.PLANNED},
        )
        exam_pk = response.json()["id"]

        self.assertEquals(response.status_code, 201)

        # Show an unprivileged user cannot create events which are not of type SELF_SERVICE_PRACTICE
        self.client.force_authenticate(user=self.student1)
        response = self.client.post(
            f"/courses/{course_pk}/events/", events.exam_1_one_at_a_time
        )
        self.assertEquals(response.status_code, 403)

        self.client.force_authenticate(user=self.teacher2)
        response = self.client.post(
            f"/courses/{course_pk}/events/", events.exam_1_one_at_a_time
        )
        self.assertEquals(response.status_code, 403)

        # Show an unprivileged user can create a SELF_SERVICE_PRACTICE
        self.client.force_authenticate(user=self.student1)
        response = self.client.post(f"/courses/{course_pk}/events/", events.practice_1)
        self.assertEquals(response.status_code, 201)
        practice_1_pk = response.json()["id"]

        self.client.force_authenticate(user=self.student2)
        response = self.client.post(f"/courses/{course_pk}/events/", events.practice_1)
        self.assertEquals(response.status_code, 201)
        practice_2_pk = response.json()["id"]

        # Show an unprivileged user cannot edit events, except for SELF_SERVICE_PRACTICE
        # created by them
        self.client.force_authenticate(user=self.student1)

        # updating an exam fails if the user doesn't have privileges
        response = self.client.patch(
            f"/courses/{course_pk}/events/{exam_pk}/", {"name": "abcdefgh"}
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.put(
            f"/courses/{course_pk}/events/{exam_pk}/",
            {**events.exam_1_all_at_once, "name": "abcdefgh"},
        )
        self.assertEquals(response.status_code, 403)

        # trying to change an event's type also fails
        response = self.client.patch(
            f"/courses/{course_pk}/events/{exam_pk}/",
            {"event_type": Event.SELF_SERVICE_PRACTICE},
        )
        self.assertEquals(response.status_code, 403)

        # updating someone else's practice fails
        response = self.client.patch(
            f"/courses/{course_pk}/events/{practice_2_pk}/", {"name": "abcdefgh"}
        )
        self.assertEquals(response.status_code, 403)

        # updating user own's practice
        response = self.client.patch(
            f"/courses/{course_pk}/events/{practice_1_pk}/", {"name": "abcdefgh"}
        )
        self.assertEquals(response.status_code, 200)

        # Show a user with `manage_events` permission can create & update events

        UserCoursePrivilege.objects.create(
            user=self.student2, course=course, allow_privileges=["manage_events"]
        )

        self.client.force_authenticate(user=self.student2)
        response = self.client.post(
            f"/courses/{course_pk}/events/",
            events.exam_1_all_at_once,
        )
        self.assertEquals(response.status_code, 201)
        response = self.client.patch(
            f"/courses/{course_pk}/events/{exam_pk}/", {"name": "abcdefgh"}
        )
        self.assertEquals(response.status_code, 200)

        # Show unprivileged users cannot access or edit the event template's rules

        self.client.force_authenticate(user=self.student1)

        template = Event.objects.get(pk=exam_pk).template

        response = self.client.get(
            f"/courses/{course_pk}/templates/{template.pk}/rules/"
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.post(
            f"/courses/{course_pk}/templates/{template.pk}/rules/",
            {"rule_type": EventTemplateRule.FULLY_RANDOM},
        )
        self.assertEquals(response.status_code, 403)

        # Show an unprivileged user can edit the template rules of a practice
        # created by them

        template = Event.objects.get(pk=practice_1_pk).template
        response = self.client.get(
            f"/courses/{course_pk}/templates/{template.pk}/rules/"
        )
        self.assertEquals(response.status_code, 200)
        response = self.client.post(
            f"/courses/{course_pk}/templates/{template.pk}/rules/",
            {"rule_type": EventTemplateRule.FULLY_RANDOM},
        )
        self.assertEquals(response.status_code, 201)

        # Show an unprivileged user cannot edit the template rules of a
        # practice created by another user

        template = Event.objects.get(pk=practice_2_pk).template
        response = self.client.get(
            f"/courses/{course_pk}/templates/{template.pk}/rules/"
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.post(
            f"/courses/{course_pk}/templates/{template.pk}/rules/",
            {"rule_type": EventTemplateRule.FULLY_RANDOM},
        )
        self.assertEquals(response.status_code, 403)

        # Show only the course creator can delete events

        self.client.force_authenticate(user=self.student1)

        response = self.client.delete(f"/courses/{course_pk}/events/{exam_pk}/")
        self.assertEquals(response.status_code, 403)
        response = self.client.delete(f"/courses/{course_pk}/events/{practice_1_pk}/")
        self.assertEquals(response.status_code, 403)
        response = self.client.delete(f"/courses/{course_pk}/events/{practice_2_pk}/")
        self.assertEquals(response.status_code, 403)

        self.client.force_authenticate(user=self.teacher2)

        response = self.client.delete(f"/courses/{course_pk}/events/{exam_pk}/")
        self.assertEquals(response.status_code, 403)
        response = self.client.delete(f"/courses/{course_pk}/events/{practice_1_pk}/")
        self.assertEquals(response.status_code, 403)
        response = self.client.delete(f"/courses/{course_pk}/events/{practice_2_pk}/")
        self.assertEquals(response.status_code, 403)

        self.client.force_authenticate(user=self.teacher1)

        response = self.client.delete(f"/courses/{course_pk}/events/{exam_pk}/")
        self.assertEquals(response.status_code, 204)
        response = self.client.delete(f"/courses/{course_pk}/events/{practice_1_pk}/")
        self.assertEquals(response.status_code, 204)
        response = self.client.delete(f"/courses/{course_pk}/events/{practice_2_pk}/")
        self.assertEquals(response.status_code, 204)


class EventParticipationViewSetTestCase(BaseTestCase):
    def setUp(self):
        from data import users, courses, exercises, events

        self.teacher_1 = User.objects.create(**users.teacher_1)
        self.course = Course.objects.create(creator=self.teacher_1, **courses.course_1)

        self.student_1 = User.objects.create(**users.student_1)
        self.student_2 = User.objects.create(**users.student_2)

        UserCourseEnrollment.objects.create(user=self.student_1, course=self.course)
        UserCourseEnrollment.objects.create(user=self.student_2, course=self.course)

        self.exercise_1 = Exercise.objects.create(
            course=self.course, **exercises.mmc_priv_1
        )
        self.exercise_2 = Exercise.objects.create(
            course=self.course, **exercises.msc_priv_1
        )
        self.event = Event.objects.create(
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

        self.client = APIClient()

    def test_participation_submission_and_assessment(self):
        self.client.force_authenticate(user=self.student_1)

        """
        Show failure to create a participation for a nonexistent Event
        """
        # response = self.client.post(
        #     f"/courses/{self.course.pk}/events/ovQqgvP/participations/"
        # )
        # self.assertEqual(response.status_code, 404)

        """
        Show users cannot participate until the exam is open
        """
        response = self.client.post(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/"
        )
        self.assertEqual(response.status_code, 403)

        self.event.state = Event.PLANNED
        self.event.begin_timestamp = timezone.localdate(timezone.now())

        self.event.access_rule = Event.DENY_ACCESS
        self.event.save()

        """
        Show unauthorized users cannot participate
        """
        response = self.client.post(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/"
        )
        self.assertEqual(response.status_code, 403)

        """
        Show an allowed user can create a participation
        """
        self.event.access_rule_exceptions = [self.student_1.email]
        self.event.save()

        response = self.client.post(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "slots")

        slots = response.data["slots"]

        # show exercise is included in the response
        # TODO show exercise isn't included when a teacher accesses the list of participations
        self.assertIn("exercise", slots[0])

        response = self.client.post(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/?include_details=true"
        )
        self.assertEqual(response.status_code, 200)
        participation_pk = response.data["id"]

        self.assertContains(response, "slots")

        slots = response.data["slots"]
        # show exercise is included in the response if asked for
        self.assertIn("exercise", slots[0])

        # show a single exercise is being shown and it's the correct one
        self.assertEqual(len(slots), 1)

        exercise = slots[0]["exercise"]
        self.assertEquals(exercise["text"], self.exercise_1.text)

        # show solution and other hidden fields aren't shown
        self.assertNotIn("score", response.data)
        self.assertNotIn("score", slots[0])
        self.assertNotIn("comment", slots[0])
        self.assertNotIn("solution", exercise)
        self.assertNotIn("correct_choices", exercise)
        self.assertNotIn("private_tags", exercise)
        self.assertNotIn("correctness", exercise["choices"][0])

        """
        Moving forward one slot
        """
        response = self.client.post(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/go_forward/"
        )
        self.assertEqual(response.status_code, 200)

        second_slot_pk = response.data["id"]

        # correctly moved forward
        exercise = response.data["exercise"]
        self.assertEquals(exercise["text"], self.exercise_2.text)
        # hidden fields not shown
        self.assertNotIn("score", response.data)
        self.assertNotIn("comment", response.data)
        self.assertNotIn("solution", exercise)
        self.assertNotIn("correct_choices", exercise)
        self.assertNotIn("private_tags", exercise)
        self.assertNotIn("correctness", exercise["choices"][0])

        # show moving back is only possible when allowed in the Event
        self.event.allow_going_back = False
        self.event.save()

        """
        Moving back
        """
        response = self.client.post(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/go_back/"
        )
        # fails because Event doesn't allow it
        self.assertEqual(response.status_code, 403)

        self.event.allow_going_back = True
        self.event.save()

        response = self.client.post(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/go_back/"
        )
        # Event now allows it
        self.assertEqual(response.status_code, 200)

        # correctly went back
        exercise = response.data["exercise"]
        self.assertEquals(exercise["text"], self.exercise_1.text)
        # hidden fields not shown
        self.assertNotIn("score", response.data)
        self.assertNotIn("comment", response.data)
        self.assertNotIn("solution", exercise)
        self.assertNotIn("correct_choices", exercise)
        self.assertNotIn("private_tags", exercise)
        self.assertNotIn("correctness", exercise["choices"][0])

        slot_pk = response.data["id"]

        """
        Show the owner of the participation can update its slot
        """
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_pk}/",
            {"selected_choices": [self.exercise_1.choices.first().pk]},
        )
        self.assertEqual(response.status_code, 200)
        exercise = response.data["exercise"]
        # still same exercise
        self.assertEquals(exercise["text"], self.exercise_1.text)
        # show hidden fields aren't showed in the response
        self.assertNotIn("score", response.data)
        self.assertNotIn("comment", response.data)
        self.assertNotIn("solution", exercise)
        self.assertNotIn("correct_choices", exercise)
        self.assertNotIn("private_tags", exercise)
        self.assertNotIn("correctness", exercise["choices"][0])

        """
        Show user cannot select choices that don't belong to the exercise or that don't exist
        """
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_pk}/",
            {"selected_choices": [self.exercise_2.choices.first().pk]},
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_pk}/",
            {"selected_choices": [123101]},
        )
        self.assertEqual(response.status_code, 400)

        """
        Show failure in updating an out-of-scope slot
        """
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{second_slot_pk}/",
            {"selected_choices": [self.exercise_2.choices.first().pk]},
        )
        self.assertEqual(response.status_code, 403)

        """
        Show a user that's not the owner of the participation cannot retrieve or
        update it and its slots
        """
        self.client.force_authenticate(self.student_2)
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_pk}/",
            {"selected_choices": [self.exercise_1.choices.first().pk]},
        )
        self.assertEqual(response.status_code, 403)

        """
        Show participations cannot be deleted by anyone
        """
        response = self.client.delete(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.student_2)
        response = self.client.delete(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
        )
        self.assertEqual(response.status_code, 403)

        """
        Show failure to update an assessment field as a student
        """
        slot_score = EventParticipationSlot.objects.get(pk=slot_pk).score
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_pk}/",
            {"score": "10.0"},
        )
        slot = EventParticipationSlot.objects.get(pk=slot_pk)
        self.assertEqual(slot.score, slot_score)

        """
        Show failure to update participation (i.e. turning it in) as a user
        that's not its owner
        """
        self.client.force_authenticate(self.student_2)
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
            {"state": EventParticipation.TURNED_IN},
        )
        self.assertEqual(response.status_code, 403)

        """
        Show turning in the participation as the correct user 
        """
        self.client.force_authenticate(self.student_1)
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
            {"state": EventParticipation.TURNED_IN},
        )
        self.assertEqual(response.status_code, 200)

        """
        Show that after it's been turned in, no fields or slots can be updated
        """
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
            {"state": EventParticipation.IN_PROGRESS},
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_pk}/",
            {"selected_choices": [self.exercise_1.choices.first().pk]},
        )
        self.assertEqual(response.status_code, 403)

        """
        Show accessing the participations before assessments have been published
        """
        response = self.client.get(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
        )

        # all slots are shown
        self.assertContains(response, "slots")
        slots = response.data["slots"]
        self.assertEqual(len(slots), 2)

        exercise = slots[0]["exercise"]
        # show solution and other hidden fields aren't shown
        self.assertNotIn("score", response.data)
        self.assertNotIn("score", slots[0])
        self.assertNotIn("comment", slots[0])
        self.assertNotIn("solution", exercise)
        self.assertNotIn("correct_choices", exercise)
        self.assertNotIn("private_tags", exercise)
        self.assertNotIn("correctness", exercise["choices"][0])

        """
        Show failure to access someone else's participation as a student
        """
        self.client.force_authenticate(self.student_2)
        response = self.client.get(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
        )
        self.assertEqual(response.status_code, 403)

        """
        Show a user with `assess_participations` permission can see the participation(s)
        """
        self.client.force_authenticate(self.teacher_1)
        response = self.client.get(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/",
        )
        self.assertEqual(response.status_code, 200)

        participations = response.data
        self.assertEqual(len(participations), 1)

        participation = participations[0]
        slots = participation["slots"]

        # show hidden fields are shown to teachers with appropriate permissions
        self.assertIn("score", participation)
        self.assertIn("score", slots[0])
        self.assertIn("comment", slots[0])

        # show "expensive" fields aren't shown if not requested when viewing
        # the list of all participations
        self.assertNotIn("exercise", slots[0])
        self.assertNotIn("answer_text", slots[0])
        self.assertNotIn("selected_choices", slots[0])
        self.assertNotIn("sub_slots", slots[0])
        self.assertNotIn("is_first", slots[0])
        self.assertNotIn("is_last", slots[0])

        # request all fields
        response = self.client.get(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/?include_details=1",
        )
        self.assertEqual(response.status_code, 200)

        participations = response.data
        self.assertEqual(len(participations), 1)

        participation = participations[0]
        slots = participation["slots"]

        # "expensive" fields are shown if requested
        self.assertIn("exercise", slots[0])
        self.assertIn("answer_text", slots[0])
        self.assertIn("selected_choices", slots[0])
        self.assertIn("sub_slots", slots[0])
        self.assertIn("is_first", slots[0])
        self.assertIn("is_last", slots[0])

        # show hidden fields are shown to teachers with appropriate permissions
        self.assertIn("score", participation)
        self.assertIn("score", slots[0])
        self.assertIn("comment", slots[0])

        # self.assertIn("solution", slots[0]["exercise"])

        self.assertIn("correctness", slots[0]["exercise"]["choices"][0])

        """
        Show a user with `assess_participations` permission can update the assessment
        related fields (and only those)
        """
        self.client.force_authenticate(self.teacher_1)
        response = self.client.get(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
        )
        self.assertEqual(response.status_code, 200)
        participation = response.data

        self.assertIn("slots", participation)
        slots = participation["slots"]

        # "expensive" fields are shown if accessing a single participation
        self.assertIn("exercise", slots[0])
        self.assertIn("answer_text", slots[0])
        self.assertIn("selected_choices", slots[0])
        self.assertIn("sub_slots", slots[0])
        self.assertIn("is_first", slots[0])
        self.assertIn("is_last", slots[0])

        # show hidden fields are shown to teachers with appropriate permissions
        self.assertIn("score", participation)
        self.assertIn("score", slots[0])
        self.assertIn("comment", slots[0])

        # self.assertIn("solution", slots[0]["exercise"])

        self.assertIn("correctness", slots[0]["exercise"]["choices"][0])

        slot_0_pk = slots[0]["id"]
        """
        A user with `assess_participations` privilege can edit assessment fields
        """
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_0_pk}/",
            {"score": "10.0", "comment": "test comment"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["score"]), Decimal("10.0"))
        self.assertEquals(response.data["comment"], "test comment")

        """
        A user with `assess_participations` privilege can publish assessments - after
        that, assessment fields can be accessed by students for their participations
        """
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
            {"visibility": EventParticipation.PUBLISHED},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["visibility"], EventParticipation.PUBLISHED)

        # failure to access someone else's participation as a student even
        # after publishing assessment
        self.client.force_authenticate(self.student_2)
        response = self.client.get(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
        )
        self.assertEqual(response.status_code, 403)

        # the owner of the participation can now see assessment fields
        self.client.force_authenticate(self.student_1)
        response = self.client.get(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/",
        )
        self.assertEqual(response.status_code, 200)

        slots = response.data["slots"]
        self.assertIn("exercise", slots[0])
        exercise = slots[0]["exercise"]

        # show hidden fields are shown
        self.assertIn("score", response.data)
        self.assertIn("score", slots[0])
        self.assertIn("comment", slots[0])
        # self.assertIn("solution", exercise)
        self.assertIn("correctness", exercise["choices"][0])

    def test_view_queryset(self):
        # show that, for each event, you can only access that events's
        # participations from the events's endpoint
        pass


class CoursePrivilegeTestCase(BaseTestCase):
    def setUp(self):
        from data import users, courses, exercises, events

        self.teacher_1 = User.objects.create(**users.teacher_1)
        self.teacher_2 = User.objects.create(**users.teacher_2)

        self.course = Course.objects.create(creator=self.teacher_1, **courses.course_1)

        self.student_1 = User.objects.create(**users.student_1)
        UserCourseEnrollment.objects.create(user=self.student_1, course=self.course)

        self.client = APIClient()

    def test_course_privileges_endpoint(self):
        """
        Show users can only access this endpoint if they have the correct permissions
        """
        course_pk = self.course.pk
        self.client.force_authenticate(self.student_1)

        # unprivileged users cannot access the endpoint
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.student_1.pk}",
            {"course_privileges": ["manage_events"]},
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.teacher_2)
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.student_1.pk}",
            {"course_privileges": ["manage_events"]},
        )
        self.assertEqual(response.status_code, 403)

        # the `update_course` privilege is required
        privileges = UserCoursePrivilege.objects.create(
            user=self.teacher_2, course=self.course, allow_privileges=["manage_events"]
        )
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.student_1.pk}",
            {"course_privileges": ["manage_events"]},
        )
        self.assertEqual(response.status_code, 403)

        privileges.allow_privileges.append("update_course")
        privileges.save()

        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.student_1.pk}",
            {"course_privileges": ["manage_events", "update_course"]},
        )
        self.assertEqual(response.status_code, 200)

        # even if a user has the correct privileges, they cannot update their privileges
        self.client.force_authenticate(self.student_1)
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.student_1.pk}",
            {"course_privileges": ["manage_events"]},
        )
        self.assertEqual(response.status_code, 403)

        # even if a user has the correct privileges, they cannot update the course creator's privileges
        self.client.force_authenticate(self.student_1)
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.teacher_1.pk}",
            {"course_privileges": ["manage_events"]},
        )
        self.assertEqual(response.status_code, 403)

        # with correct privileges, user can update another user's privileges
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.teacher_2.pk}",
            {"course_privileges": ["manage_events", "update_course"]},
        )
        self.assertEqual(response.status_code, 200)

        """
        Show how the `email` param can be used to assign privileges to
        users that don't exist yet
        """
        email = "test@gmail.com"

        self.assertFalse(User.objects.filter(email=email).exists())

        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?email={email}",
            {
                "course_privileges": [
                    "manage_events",
                    "manage_exercises",
                    "access_exercises",
                ]
            },
        )
        self.assertEqual(response.status_code, 200)

        # the id of the new user is returned in the response
        self.assertContains(response, "id")

        # user was created with given email
        self.assertEqual(User.objects.filter(email=email).count(), 1)
        # user has been assigned the correct privileges
        privileges = UserCoursePrivilege.objects.get(
            user__email=email, course=self.course
        )
        self.assertListEqual(
            privileges.allow_privileges,
            ["manage_events", "manage_exercises", "access_exercises"],
        )

        """
        Show failure conditions
        """
        # not providing a user_id param
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/",
            {"course_privileges": ["manage_events"]},
        )
        self.assertEqual(response.status_code, 400)

        # invalid privileges
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.teacher_2.pk}",
            {"course_privileges": ["manage_events", "abc"]},
        )
        self.assertEqual(response.status_code, 400)

        # invalid payload
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id={self.teacher_2.pk}",
            {"course_privilegesaa": 1},
        )
        self.assertEqual(response.status_code, 400)

        # nonexisting user
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?user_id=11111111",
            {"course_privileges": ["manage_events", "update_course"]},
        )
        self.assertEqual(response.status_code, 404)

        # invalid email
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?email=11111111",
            {"course_privileges": ["manage_events", "update_course"]},
        )
        self.assertEqual(response.status_code, 400)

        # email of existing user
        response = self.client.patch(
            f"/courses/{course_pk}/privileges/?email={self.teacher_1.email}",
            {"course_privileges": ["manage_events", "update_course"]},
        )
        self.assertEqual(response.status_code, 400)


class BulkActionsMixinsTestCase(BaseTestCase):
    def setUp(self):
        from data import users, courses, exercises, events

        self.teacher_1 = User.objects.create(**users.teacher_1)
        self.course = Course.objects.create(creator=self.teacher_1, **courses.course_1)

        self.student_1 = User.objects.create(**users.student_1)
        self.student_2 = User.objects.create(**users.student_2)
        self.student_3 = User.objects.create(**users.student_3)

        UserCourseEnrollment.objects.create(user=self.student_1, course=self.course)
        UserCourseEnrollment.objects.create(user=self.student_2, course=self.course)
        UserCourseEnrollment.objects.create(user=self.student_3, course=self.course)

        self.exercise_1 = Exercise.objects.create(
            course=self.course, **exercises.mmc_priv_1
        )
        self.exercise_2 = Exercise.objects.create(
            course=self.course, **exercises.msc_priv_1
        )
        self.exercise_3 = Exercise.objects.create(
            course=self.course, **exercises.mmc_pub_1
        )
        self.exercise_4 = Exercise.objects.create(
            course=self.course, **exercises.msc_pub_1
        )
        self.event = Event.objects.create(
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

        self.participation_1 = EventParticipation.objects.create(
            event_id=self.event.pk, user=self.student_1
        )
        self.participation_2 = EventParticipation.objects.create(
            event_id=self.event.pk, user=self.student_2
        )
        self.client = APIClient()

    def test_bulk_get(self):
        """
        Show unprivileged users can bulk get exercises only if visible to them, whereas
        users with `access_exercises` privilege can bulk get all exercises in the course
        """
        course_pk = self.course.pk

        # unprivileged user
        self.client.force_authenticate(self.student_3)

        # all not_visible_by
        response = self.client.get(
            f"/courses/{course_pk}/exercises/bulk_get/?ids={self.exercise_1.pk},{self.exercise_2.pk}",
        )
        self.assertEqual(response.status_code, 404)

        # one of the two is not visible
        response = self.client.get(
            f"/courses/{course_pk}/exercises/bulk_get/?ids={self.exercise_3.pk},{self.exercise_2.pk}",
        )
        self.assertEqual(response.status_code, 404)

        # all exercises visible
        response = self.client.get(
            f"/courses/{course_pk}/exercises/bulk_get/?ids={self.exercise_3.pk},{self.exercise_4.pk}",
        )
        self.assertEqual(response.status_code, 200)

        # privileged user
        self.client.force_authenticate(self.teacher_1)
        response = self.client.get(
            f"/courses/{course_pk}/exercises/bulk_get/?ids={self.exercise_1.pk},{self.exercise_2.pk}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], self.exercise_1.pk)
        self.assertEqual(response.data[1]["id"], self.exercise_2.pk)

        """
        Malformed requests
        """
        response = self.client.get(
            f"/courses/{course_pk}/exercises/bulk_get/?fdfgsfgesg={self.exercise_1.pk},{self.exercise_2.pk}",
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.get(
            f'/courses/{course_pk}/exercises/bulk_get/?ids=" DROP TABLE courses.exercise;',
        )
        self.assertEqual(response.status_code, 400)

    def test_bulk_patch(self):
        """
        Show students cannot bulk patch participations and users
        with `assess_participations` privilege can
        """
        course_pk = self.course.pk
        event_pk = self.event.pk

        self.client.force_authenticate(self.student_1)
        response = self.client.patch(
            f"/courses/{course_pk}/events/{event_pk}/participations/bulk_patch/?ids={self.participation_1.pk},{self.participation_2.pk}",
            {"visibility": EventParticipation.PUBLISHED},
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.teacher_1)
        response = self.client.patch(
            f"/courses/{course_pk}/events/{event_pk}/participations/bulk_patch/?ids={self.participation_1.pk},{self.participation_2.pk}",
            {"visibility": EventParticipation.PUBLISHED},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["visibility"], EventParticipation.PUBLISHED)
        self.assertEqual(response.data[1]["visibility"], EventParticipation.PUBLISHED)

        """
        Malformed requests
        """
        response = self.client.patch(
            f"/courses/{course_pk}/events/{event_pk}/participations/bulk_patch/?ierstgrwetds={self.participation_1.pk},{self.participation_2.pk}",
            {"visibility": EventParticipation.PUBLISHED},
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            f'/courses/{course_pk}/events/{event_pk}/participations/bulk_patch/?ids=" DROP TABLE users.user;',
            {"visibility": EventParticipation.PUBLISHED},
        )
        self.assertEqual(response.status_code, 400)
