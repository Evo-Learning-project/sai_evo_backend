from datetime import timedelta
from django.test import TestCase
from course_tree.models import AnnouncementNode, LessonNode, RootCourseTreeNode
from courses.models import Course, Event
from integrations.classroom import messages

from integrations.classroom.integration import GoogleClassroomIntegration

from courses.tests.data import users, courses, events
from integrations.classroom.models import GoogleClassroomCourseTwin
from integrations.registry import IntegrationRegistry
from users.models import User

from unittest.mock import Mock, patch

from django.utils import timezone

patch_get_service = patch(
    "integrations.classroom.integration.GoogleClassroomIntegration.get_service"
)


class ClassroomIntegrationTestCase(TestCase):
    def setUp(self):
        self.integration = GoogleClassroomIntegration()
        self.teacher_1 = User.objects.create(**users.teacher_1)
        self.student_1 = User.objects.create(**users.student_1)
        self.student_2 = User.objects.create(**users.student_2)
        self.student_3 = User.objects.create(**users.student_3)
        self.course = Course.objects.create(**courses.course_1)
        self.course_no_integration = Course.objects.create(**courses.course_2)

        mock_classroom_course = {
            "id": "541942443924",
            "name": "test",
            "description": "Test description. 123 abc",
            "enrollmentCode": "autrwoi",
            "alternateLink": "https://classroom.google.com/c/NTWyNDQyNDQzOTQ3",
        }

        self.classroom_course_twin = (
            GoogleClassroomCourseTwin.create_from_remote_object(
                course=self.course,
                remote_object=mock_classroom_course,
                fallback_user=self.teacher_1,
                remote_object_id=mock_classroom_course["id"],
            )
        )

    def test_integration_is_active(self):
        self.assertIn(
            GoogleClassroomIntegration,
            IntegrationRegistry().get_enabled_integrations_for(self.course),
        )

    @patch_get_service
    def test_on_exam_published(self, mock_get_service):
        mock_service = Mock()
        mock_create = mock_service.courses().courseWork().create
        mock_create.return_value.execute.return_value = {"id": "5678"}
        mock_get_service.return_value = mock_service

        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        one_hour_from_now = timezone.now() + timedelta(hours=1)

        exam_1 = Event.objects.create(
            **{
                "name": "exam_1",
                "event_type": Event.EXAM,
                "exercises_shown_at_a_time": None,
                "begin_timestamp": five_minutes_ago,
                "state": Event.PLANNED,
            },
            course=self.course,
        )

        # Call the method under test
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            self.integration.on_exam_published(self.teacher_1, exam_1)

        # Check that the Classroom API was called with the correct parameters
        mock_create.assert_called_with(
            courseId=self.classroom_course_twin.remote_object_id,
            body={
                "title": exam_1.name,
                "description": messages.get_message(messages.EXAM_PUBLISHED),
                # if the begin_timestamp is in the past, the exam is published immediately
                "state": "PUBLISHED",
                "maxPoints": exam_1.max_score,
                "workType": "ASSIGNMENT",
                "materials": [{"link": {"url": exam_1.get_absolute_url()}}],
            },
        )

        exam_2 = Event.objects.create(
            **{
                "name": "exam_2",
                "event_type": Event.EXAM,
                "exercises_shown_at_a_time": None,
                "begin_timestamp": one_hour_from_now,
                "state": Event.PLANNED,
            },
            course=self.course,
        )

        # Call the method under test
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            self.integration.on_exam_published(self.teacher_1, exam_2)

        # Check that the Classroom API was called with the correct parameters
        mock_create.assert_called_with(
            courseId=self.classroom_course_twin.remote_object_id,
            body={
                "title": exam_2.name,
                "description": messages.get_message(messages.EXAM_PUBLISHED),
                "state": "DRAFT",
                "scheduledTime": exam_2.begin_timestamp.isoformat(),
                "maxPoints": exam_2.max_score,
                "workType": "ASSIGNMENT",
                "materials": [{"link": {"url": exam_2.get_absolute_url()}}],
            },
        )

    @patch_get_service
    def test_on_exam_published(self, mock_get_service):
        mock_service = Mock()
        # mock the API call to create a new CourseWork
        mock_create = mock_service.courses().courseWork().create
        # mock the CourseWork dict returned by the Classroom API
        mock_create.return_value.execute.return_value = {"id": "5678"}
        mock_get_service.return_value = mock_service

        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        one_hour_from_now = timezone.now() + timedelta(hours=1)

        exam_1 = Event.objects.create(
            **{
                "name": "exam_1",
                "event_type": Event.EXAM,
                "exercises_shown_at_a_time": None,
                "begin_timestamp": five_minutes_ago,
                "state": Event.PLANNED,
            },
            course=self.course,
        )

        # Call the method under test
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            self.integration.on_exam_published(self.teacher_1, exam_1)

        # Check that the Classroom API was called with the correct parameters
        mock_create.assert_called_with(
            courseId=self.classroom_course_twin.remote_object_id,
            body={
                "title": exam_1.name,
                "description": messages.get_message(messages.EXAM_PUBLISHED),
                # if the begin_timestamp is in the past, the exam is published immediately
                "state": "PUBLISHED",
                "maxPoints": exam_1.max_score,
                "workType": "ASSIGNMENT",
                "materials": [{"link": {"url": exam_1.get_absolute_url()}}],
            },
        )

        exam_2 = Event.objects.create(
            **{
                "name": "exam_2",
                "event_type": Event.EXAM,
                "exercises_shown_at_a_time": None,
                "begin_timestamp": one_hour_from_now,
                "state": Event.PLANNED,
            },
            course=self.course,
        )

        # Call the method under test
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            self.integration.on_exam_published(self.teacher_1, exam_2)

        # Check that the Classroom API was called with the correct parameters
        mock_create.assert_called_with(
            courseId=self.classroom_course_twin.remote_object_id,
            body={
                "title": exam_2.name,
                "description": messages.get_message(messages.EXAM_PUBLISHED),
                "state": "DRAFT",
                "scheduledTime": exam_2.begin_timestamp.isoformat(),
                "maxPoints": exam_2.max_score,
                "workType": "ASSIGNMENT",
                "materials": [{"link": {"url": exam_2.get_absolute_url()}}],
            },
        )

    @patch_get_service
    def test_on_exam_published(self, mock_get_service):
        mock_service = Mock()
        # mock the API call to create a new CourseWorkMaterial
        mock_create = mock_service.courses().courseWorkMaterials().create
        # mock the CourseWorkMaterial dict returned by the Classroom API
        mock_create.return_value.execute.return_value = {"id": "5678"}
        mock_get_service.return_value = mock_service

        root = RootCourseTreeNode.objects.create(course=self.course)
        lesson_1 = LessonNode.objects.create(
            **{
                "title": "lesson_1",
                "body": "body",
                "state": LessonNode.LessonState.PUBLISHED,
            },
            parent=root,
        )

        # Call the method under test
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            self.integration.on_lesson_published(self.teacher_1, lesson_1)

        # Check that the Classroom API was called with the correct parameters
        mock_create.assert_called_with(
            courseId=self.classroom_course_twin.remote_object_id,
            body={
                "title": "lesson_1",
                "description": messages.get_message(messages.VIEW_LESSON_ON_EVO),
                "state": "PUBLISHED",
                "materials": [
                    {"link": {"url": lesson_1.get_absolute_url()}},
                ],
            },
        )

    @patch_get_service
    def test_on_exam_published(self, mock_get_service):
        mock_service = Mock()
        # mock the API call to create a new Announcement
        mock_create = mock_service.courses().announcements().create
        # mock the Announcement dict returned by the Classroom API
        mock_create.return_value.execute.return_value = {"id": "5678"}
        mock_get_service.return_value = mock_service

        root = RootCourseTreeNode.objects.create(course=self.course)
        announcement_1 = AnnouncementNode.objects.create(
            **{
                "body": "body announcement_1",
                "state": AnnouncementNode.AnnouncementState.PUBLISHED,
            },
            parent=root,
        )

        # Call the method under test
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            self.integration.on_announcement_published(self.teacher_1, announcement_1)

        # Check that the Classroom API was called with the correct parameters
        mock_create.assert_called_with(
            courseId=self.classroom_course_twin.remote_object_id,
            body={
                "text": "body announcement_1",
                "state": "PUBLISHED",
                "assigneeMode": "ALL_STUDENTS",
                "materials": [
                    {"link": {"url": announcement_1.get_absolute_url()}},
                ],
            },
        )
