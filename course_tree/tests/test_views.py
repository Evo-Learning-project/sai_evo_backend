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

from course_tree.models import (
    AnnouncementNode,
    PollNode,
    LessonNode,
    TopicNode,
    FileNode,
)


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
        topic_lesson2_id = response.json()["id"]
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
            set([topic_lesson2_id, topic_id, lesson1_id, root_id]),
            set([n["id"] for n in res_data]),
        )

        # test top_level only returns direct children of root
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertListEqual([topic_id, lesson1_id], [n["id"] for n in res_data])

        # create a few more nodes
        lesson2_id = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.lesson_node_2, "parent_id": root_id},
        ).json()["id"]
        poll1_id = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.poll_node_1, "parent_id": root_id},
        ).json()["id"]
        announcement1_id = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.announcement_node_1, "parent_id": root_id},
        ).json()["id"]

        # show a user without privileges cannot see draft nodes
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertNotIn(lesson1_id, [n["id"] for n in res_data])
        self.assertNotIn(poll1_id, [n["id"] for n in res_data])
        self.assertNotIn(announcement1_id, [n["id"] for n in res_data])
        self.assertIn(topic_id, [n["id"] for n in response.json()["results"]])

        # show a user with privileges can access draft nodes
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertIn(lesson1_id, [n["id"] for n in res_data])
        self.assertIn(poll1_id, [n["id"] for n in res_data])
        self.assertIn(announcement1_id, [n["id"] for n in res_data])
        self.assertIn(topic_id, [n["id"] for n in response.json()["results"]])

        # make draft nodes public
        LessonNode.objects.filter(pk=lesson1_id).update(
            state=LessonNode.LessonState.PUBLISHED
        )
        AnnouncementNode.objects.filter(pk=announcement1_id).update(
            state=AnnouncementNode.AnnouncementState.PUBLISHED
        )
        PollNode.objects.filter(pk=poll1_id).update(state=PollNode.PollState.OPEN)

        # nodes that were hidden are now visible
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertIn(lesson1_id, [n["id"] for n in res_data])
        self.assertIn(poll1_id, [n["id"] for n in res_data])
        self.assertIn(announcement1_id, [n["id"] for n in res_data])
        self.assertIn(topic_id, [n["id"] for n in response.json()["results"]])

        """
        Test ordering of nodes
        """
        self.client.force_authenticate(user=self.teacher1)

        # show nodes are retrieved in the correct order
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertListEqual(
            [
                announcement1_id,
                poll1_id,
                lesson2_id,
                topic_id,
                lesson1_id,
            ],
            [n["id"] for n in res_data],
        )

        """
        Show reordering of nodes
        """

        # move last node to left of second-to-last node
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{announcement1_id}/move/?target={poll1_id}&position=right"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertListEqual(
            [
                poll1_id,
                announcement1_id,
                lesson2_id,
                topic_id,
                lesson1_id,
            ],
            [n["id"] for n in res_data],
        )

        # move a node to be the first child
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{topic_id}/move/?target={root_id}&position=first-child"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertListEqual(
            [
                topic_id,
                poll1_id,
                announcement1_id,
                lesson2_id,
                lesson1_id,
            ],
            [n["id"] for n in res_data],
        )

        # move a node to be the last child
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{announcement1_id}/move/?target={root_id}&position=last-child"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertListEqual(
            [
                topic_id,
                poll1_id,
                lesson2_id,
                lesson1_id,
                announcement1_id,
            ],
            [n["id"] for n in res_data],
        )

        # move a node to have a different parent
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{announcement1_id}/move/?target={topic_id}&position=first-child"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/?top_level=true")
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        # node isn't top level anymore
        self.assertListEqual(
            [
                topic_id,
                poll1_id,
                lesson2_id,
                lesson1_id,
            ],
            [n["id"] for n in res_data],
        )

        # node is found among children of the new parent

        response = self.client.get(
            f"/courses/{self.course.pk}/nodes/{topic_id}/children/"
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()["results"]
        self.assertListEqual(
            [announcement1_id, topic_lesson2_id],
            [n["id"] for n in res_data],
        )

        """
        Test update of nodes
        """

        # show a user with privileges can update a node
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.patch(
            f"/courses/{self.course.pk}/nodes/{lesson1_id}/", {"title": "updated"}
        )
        self.assertEqual(response.status_code, 200)

        # show a user without privileges cannot update a node
        self.client.force_authenticate(user=self.student1)
        response = self.client.patch(
            f"/courses/{self.course.pk}/nodes/{lesson1_id}/", {"title": "updated 2"}
        )
        self.assertEqual(response.status_code, 403)

        """
        Test deletion of nodes
        """

        # show a user with privileges can delete a node
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(f"/courses/{self.course.pk}/nodes/{lesson1_id}/")
        self.assertEqual(response.status_code, 204)

        # show a user without privileges cannot  delete a node
        self.client.force_authenticate(user=self.student1)
        response = self.client.delete(f"/courses/{self.course.pk}/nodes/{lesson1_id}/")
        self.assertEqual(response.status_code, 403)

        # show nobody can delete or update the root node
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(f"/courses/{self.course.pk}/nodes/{root_id}/")
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            f"/courses/{self.course.pk}/nodes/{root_id}/", {"creator": self.student1.pk}
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.student1)
        response = self.client.delete(f"/courses/{self.course.pk}/nodes/{root_id}/")
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            f"/courses/{self.course.pk}/nodes/{root_id}/", {"creator": self.student1.pk}
        )
        self.assertEqual(response.status_code, 403)

    # TODO write test for file nodes, especially the download view

    def test_comments(self):
        # create a node first
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/root_id/")
        self.assertEquals(response.status_code, 200)
        root_id = response.json()

        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.lesson_node_3, "parent_id": root_id},
        )
        lesson_id = response.json()["id"]
        self.assertEquals(response.status_code, 201)

        """
        Show unprivileged users cannot comment on non-public nodes
        """
        # TODO
        # self.client.force_authenticate(user=self.student1)
        # response = self.client.post(
        #     f"/courses/{self.course.pk}/nodes/{lesson_id}/comments/",
        #     {"comment": "not gonna work"},
        # )
        # self.assertEquals(response.status_code, 404)

        LessonNode.objects.filter(pk=lesson_id).update(
            state=LessonNode.LessonState.PUBLISHED
        )

        """
        Show users can comment nodes
        """
        self.client.force_authenticate(user=self.student1)
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{lesson_id}/comments/",
            {"comment": "123 abc"},
        )
        comment1_id = response.json()["id"]
        self.assertEquals(response.status_code, 201)

        self.client.force_authenticate(user=self.student2)
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{lesson_id}/comments/",
            {"comment": "345 abc"},
        )
        comment2_id = response.json()["id"]
        self.assertEquals(response.status_code, 201)

        # show an unprivileged user cannot update or delete somebody else's comments
        self.client.force_authenticate(user=self.student1)
        response = self.client.patch(
            f"/courses/{self.course.pk}/nodes/{lesson_id}/comments/{comment2_id}/",
            {"comment": "123 abc updated"},
        )
        self.assertEquals(response.status_code, 403)
        response = self.client.delete(
            f"/courses/{self.course.pk}/nodes/{lesson_id}/comments/{comment2_id}/",
        )
        self.assertEquals(response.status_code, 403)

        # show a user can delete their comments
        response = self.client.delete(
            f"/courses/{self.course.pk}/nodes/{lesson_id}/comments/{comment1_id}/",
        )
        self.assertEquals(response.status_code, 204)

    def test_poll(self):
        # create a poll first
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(f"/courses/{self.course.pk}/nodes/root_id/")
        self.assertEquals(response.status_code, 200)
        root_id = response.json()
        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/",
            {**data.poll_node_1, "parent_id": root_id},
        )
        poll_id = response.json()["id"]
        self.assertEquals(response.status_code, 201)

        response = self.client.get(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/"
        )
        self.assertEquals(response.status_code, 200)
        # no choices initially
        self.assertEqual(len(response.json()), 0)

        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/", {"text": "choice 1"}
        )
        self.assertEquals(response.status_code, 201)
        choice1_id = response.json()["id"]

        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/", {"text": "choice 2"}
        )
        self.assertEquals(response.status_code, 201)
        choice2_id = response.json()["id"]

        response = self.client.post(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/", {"text": "choice 3"}
        )
        self.assertEquals(response.status_code, 201)
        choice3_id = response.json()["id"]

        response = self.client.get(f"/courses/{self.course.pk}/nodes/{poll_id}/")
        self.assertEquals(response.status_code, 200)
        choices_data = response.json()["choices"]

        self.assertEqual(choices_data[0]["id"], choice1_id)
        self.assertEqual(choices_data[0]["votes"], 0)
        self.assertFalse(choices_data[0]["selected"])
        self.assertEqual(choices_data[1]["id"], choice2_id)
        self.assertEqual(choices_data[1]["votes"], 0)
        self.assertFalse(choices_data[1]["selected"])
        self.assertEqual(choices_data[2]["id"], choice3_id)
        self.assertEqual(choices_data[2]["votes"], 0)
        self.assertFalse(choices_data[2]["selected"])

        response = self.client.put(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/{choice1_id}/vote/"
        )
        self.assertEquals(response.status_code, 200)

        response = self.client.get(f"/courses/{self.course.pk}/nodes/{poll_id}/")
        self.assertEquals(response.status_code, 200)
        choices_data = response.json()["choices"]

        # choice now has one vote and is marked as voted by the requesting user
        self.assertEqual(choices_data[0]["id"], choice1_id)
        self.assertEqual(choices_data[0]["votes"], 1)
        self.assertTrue(choices_data[0]["selected"])

        self.assertEqual(choices_data[1]["id"], choice2_id)
        self.assertEqual(choices_data[1]["votes"], 0)
        self.assertFalse(choices_data[1]["selected"])
        self.assertEqual(choices_data[2]["id"], choice3_id)
        self.assertEqual(choices_data[2]["votes"], 0)
        self.assertFalse(choices_data[2]["selected"])

        self.client.force_authenticate(user=self.student1)

        # unauthorized users cannot vote since the poll isn't open yet
        response = self.client.put(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/{choice1_id}/vote/"
        )
        self.assertEquals(response.status_code, 403)

        PollNode.objects.filter(pk=poll_id).update(state=PollNode.PollState.CLOSED)

        # still can't vote as the poll is closed
        response = self.client.put(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/{choice1_id}/vote/"
        )
        self.assertEquals(response.status_code, 403)

        PollNode.objects.filter(pk=poll_id).update(state=PollNode.PollState.OPEN)

        response = self.client.get(f"/courses/{self.course.pk}/nodes/{poll_id}/")
        self.assertEquals(response.status_code, 200)
        choices_data = response.json()["choices"]

        # requesting user hasn't voted yet - votes for each choice aren't displayed
        self.assertEqual(choices_data[0]["id"], choice1_id)
        self.assertNotIn("votes", choices_data[0])
        self.assertFalse(choices_data[0]["selected"])

        self.assertEqual(choices_data[1]["id"], choice2_id)
        self.assertNotIn("votes", choices_data[1])
        self.assertFalse(choices_data[1]["selected"])
        self.assertEqual(choices_data[2]["id"], choice3_id)
        self.assertNotIn("votes", choices_data[2])
        self.assertFalse(choices_data[2]["selected"])

        # poll is open and user can now vote
        response = self.client.put(
            f"/courses/{self.course.pk}/nodes/{poll_id}/choices/{choice1_id}/vote/"
        )
        self.assertEquals(response.status_code, 200)

        # choice data is updated with new vote
        response = self.client.get(f"/courses/{self.course.pk}/nodes/{poll_id}/")
        self.assertEquals(response.status_code, 200)
        choices_data = response.json()["choices"]

        # choice now has one vote and is marked as voted by the requesting user
        self.assertEqual(choices_data[0]["id"], choice1_id)
        self.assertEqual(choices_data[0]["votes"], 2)
        self.assertTrue(choices_data[0]["selected"])

        self.assertEqual(choices_data[1]["id"], choice2_id)
        self.assertEqual(choices_data[1]["votes"], 0)
        self.assertFalse(choices_data[1]["selected"])
        self.assertEqual(choices_data[2]["id"], choice3_id)
        self.assertEqual(choices_data[2]["votes"], 0)
        self.assertFalse(choices_data[2]["selected"])
