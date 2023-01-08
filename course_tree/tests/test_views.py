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
    UserCoursePrivilege,
)
from django.test import TestCase
from rest_framework.test import APIClient, force_authenticate
from users.models import User
import data


class BaseTestCase(TestCase):
    def setUp(self):
        from courses.tests.data import courses

        self.client = APIClient()
        self.teacher1 = User.objects.create(username="teacher1", is_teacher=True)
        self.student1 = User.objects.create(username="student1", is_teacher=False)
        self.teacher2 = User.objects.create(username="teacher2", is_teacher=True)
        self.student2 = User.objects.create(username="student2", is_teacher=False)
        self.course = Course.objects.create(creator=self.teacher1, **courses.course_1)


class TreeNodeViewSetTestCase(BaseTestCase):
    def test_CRUD(self):
        """
        Test creation of nodes
        """
        # show a user with privileges can create nodes
        self.client.force_authenticate(user=self.teacher1)

        # create root id
        response = self.client.get(f"/courses/{self.course.pk}/nodes/root_id/")
        self.assertEquals(response.status_code, 200)
        root_id = response.json()

        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.lesson_node_1, "parent_id": root_id},
        )
        lesson1_id = response.json()["id"]

        self.assertEquals(response.status_code, 201)

        # show a user without privileges cannot create nodes

        self.client.force_authenticate(user=self.student1)
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.lesson_node_1, "parent_id": root_id},
        )
        self.assertEquals(response.status_code, 403)

        # show creation of nodes that are children of other nodes other than the root

        self.client.force_authenticate(user=self.teacher1)
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.topic_node_1, "parent_id": root_id},
        )
        self.assertEquals(response.status_code, 201)
        topic_id = response.json()["id"]

        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.lesson_node_2, "parent_id": topic_id},
        )
        lesson2_id = response.json()["id"]
        self.assertEquals(response.status_code, 201)

        # invalid resourcetype
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.lesson_node_2, "parent_id": topic_id, "resourcetype": "abc"},
        )
        self.assertEquals(response.status_code, 400)

        """
        Test scoping of nodes
        """

        response = self.client.get(f"/courses/{self.course.pk}/nodes/")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertSetEqual(
            set([lesson2_id, topic_id, lesson1_id, root_id]),
            set([n["id"] for n in res_data]),
        )

        # test top_level only returns direct children of root
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertListEqual([topic_id, lesson1_id], [n["id"] for n in res_data])

        # show a user without privileges cannot see draft nodes
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertNotIn(lesson1_id, [n["id"] for n in res_data])
        self.assertIn(topic_id, [n["id"] for n in response.json()["results"]])

        """
        Test ordering of nodes
        """

        # show nodes are retrieved in the correct order

        # show reordering of nodes

        """
        Test update of nodes
        """

        # show a user with privileges can update a node

        # show a user without privileges cannot update a node

        """
        Test deletion of nodes
        """

        # show a user with privileges can delete a node

        # show a user without privileges cannot  delete a node

        pass

    def test_comments(self):
        pass

    def test_poll(self):
        pass
