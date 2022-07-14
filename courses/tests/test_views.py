from decimal import Decimal
from django.utils import timezone
from courses.logic import privileges
from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventParticipationSlot,
    EventTemplateRule,
    Exercise,
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
        choice1 = {"text": "c1", "correctness_percentage": "-70"}
        choice2 = {"text": "c2", "correctness_percentage": "100"}
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
            {"text": "new choice", "correctness_percentage": "100"},
        )
        self.assertEquals(response.status_code, 201)
        choice_pk = response.data["id"]

        response = self.client.put(
            f"/courses/{course_pk}/exercises/{exercise_pk}/choices/{choice_pk}/",
            {
                "text": "new choice text",
                "correctness_percentage": "50",
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
    def setUp(self):
        from data import users, courses, exercises, events

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
        self.assertNotIn("correctness_percentage", exercise["choices"][0])

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
        self.assertNotIn("correctness_percentage", exercise["choices"][0])

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
        self.assertNotIn("correctness_percentage", exercise["choices"][0])

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
        self.assertNotIn("correctness_percentage", exercise["choices"][0])

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
        self.assertNotIn("correctness_percentage", exercise["choices"][0])

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

        self.assertIn("solution", slots[0]["exercise"])

        self.assertIn("correctness_percentage", slots[0]["exercise"]["choices"][0])

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

        self.assertIn("solution", slots[0]["exercise"])

        self.assertIn("correctness_percentage", slots[0]["exercise"]["choices"][0])

        slot_0_pk = slots[0]["id"]
        """
        A user with `assess_participations` privilege can edit assessment fields
        """
        response = self.client.patch(
            f"/courses/{self.course.pk}/events/{self.event.pk}/participations/{participation_pk}/slots/{slot_0_pk}/",
            {"score": "10.0", "comment": "test comment"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["score"], "10.0")
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

        # show solution and other hidden fields are shown
        self.assertIn("score", response.data)
        self.assertIn("score", slots[0])
        self.assertIn("comment", slots[0])
        self.assertIn("solution", exercise)
        self.assertIn("correctness_percentage", exercise["choices"][0])

    def test_view_queryset(self):
        # show that, for each event, you can only access that events's
        # participations from the events's endpoint
        pass


class BulkActionsMixinsTestCase(BaseTestCase):
    def setUp(self):
        from data import users, courses, exercises, events

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
        Show students cannot bulk get exercises and users
        with `access_exercises` privilege can
        """
        course_pk = self.course.pk

        self.client.force_authenticate(self.student_1)
        response = self.client.get(
            f"/courses/{course_pk}/exercises/bulk_get/?ids={self.exercise_1.pk},{self.exercise_2.pk}",
        )
        self.assertEqual(response.status_code, 403)

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
