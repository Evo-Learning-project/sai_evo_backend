from datetime import timedelta
from django.test import TestCase

from course_tree.models import AnnouncementNode, LessonNode, RootCourseTreeNode
from courses.models import Course, Event, EventParticipation
from integrations.classroom import messages
from integrations.classroom.exceptions import CannotEnrollTeacher, DomainSettingsError
from googleapiclient.errors import HttpError

from integrations.classroom.integration import GoogleClassroomIntegration

from courses.tests.data import users, courses, events
from integrations.classroom.models import (
    GoogleClassroomCourseTwin,
    GoogleClassroomCourseWorkSubmissionTwin,
    GoogleClassroomCourseWorkTwin,
)
from integrations.registry import IntegrationRegistry
from users.models import User

from unittest.mock import Mock, patch

from django.utils import timezone

patch_get_service = patch(
    "integrations.classroom.integration.GoogleClassroomIntegration.get_service"
)

patch_get_classroom_course_from_evo_course = patch(
    "integrations.classroom.integration.GoogleClassroomIntegration"
    ".get_classroom_course_from_evo_course"
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
        self.assertNotIn(
            GoogleClassroomIntegration,
            IntegrationRegistry().get_enabled_integrations_for(
                self.course_no_integration
            ),
        )

    def test_on_exam_published(self):
        mock_service = Mock()
        # mock the API call to create a new CourseWork
        mock_create = mock_service.courses().courseWork().create
        # mock the CourseWork dict returned by the Classroom API
        mock_create.return_value.execute.return_value = {"id": "5678"}

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
        mock_create.assert_called_once_with(
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

        mock_create.reset_mock()

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
        mock_create.assert_called_once_with(
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

    def test_on_lesson_published(self):
        mock_service = Mock()
        # mock the API call to create a new CourseWorkMaterial
        mock_create = mock_service.courses().courseWorkMaterials().create
        # mock the CourseWorkMaterial dict returned by the Classroom API
        mock_create.return_value.execute.return_value = {"id": "5678"}

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
        mock_create.assert_called_once_with(
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

    def test_on_announcement_published(self):
        mock_service = Mock()
        # mock the API call to create a new Announcement
        mock_create = mock_service.courses().announcements().create
        # mock the Announcement dict returned by the Classroom API
        mock_create.return_value.execute.return_value = {"id": "5678"}

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
        mock_create.assert_called_once_with(
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

    def test_enroll_student(
        self,
        #   mock_get_classroom_course_from_evo_course,
    ):
        mock_service = Mock()
        # mock the API call to create a new Student
        mock_create = mock_service.courses().students().create
        # mock the Student dict returned by the Classroom API
        mock_create.return_value.execute.return_value = {"id": "5678"}

        # # mock the ClassroomCourseTwin returned
        # mock_get_classroom_course_from_evo_course.return_value = (
        #     self.classroom_course_twin
        # )

        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            self.integration.enroll_student(self.student_1, self.course)

        # Check that the Classroom API was called with the correct parameters
        mock_create.assert_called_once_with(
            courseId=self.classroom_course_twin.remote_object_id,
            enrollmentCode=self.classroom_course_twin.data["enrollmentCode"],
            body={
                "userId": self.student_1.email,
            },
        )
        mock_create.reset_mock()

        # Show that, if a 400 error with message starting with
        # @DomainSettingsError is raised, the method raises
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            mock_create.return_value.execute.side_effect = HttpError(
                resp=Mock(
                    status=400,
                    reason="@DomainSettingsError: The domain settings for this course do not allow students to be added.",
                ),
                content=b"",
            )
            with self.assertRaises(DomainSettingsError):
                self.integration.enroll_student(self.student_1, self.course)

        # Show that, if 409 is raised, the method raises if the user is a teacher
        with patch.object(self.integration, "get_service") as get_service_mock:
            with patch.object(
                self.integration, "is_teacher_on_classroom_course"
            ) as is_teacher_on_classroom_course_mock:
                get_service_mock.return_value = mock_service
                is_teacher_on_classroom_course_mock.return_value = True
                mock_create.return_value.execute.side_effect = HttpError(
                    resp=Mock(
                        status=409,
                        reason="",
                    ),
                    content=b"",
                )
                with self.assertRaises(CannotEnrollTeacher):
                    self.integration.enroll_student(self.student_1, self.course)

        # Show that, if 409 is raised, the method looks for the existing
        # enrollment and returns it if the user is a student
        with patch.object(self.integration, "get_service") as get_service_mock:
            with patch.object(
                self.integration, "is_teacher_on_classroom_course"
            ) as is_teacher_on_classroom_course_mock:
                # set up mocks to raise a 409 for a non-teacher user
                get_service_mock.return_value = mock_service
                is_teacher_on_classroom_course_mock.return_value = False
                mock_create.return_value.execute.side_effect = HttpError(
                    resp=Mock(
                        status=409,
                        reason="",
                    ),
                    content=b"",
                )
                mock_get_student = mock_service.courses().students().get

                # call the method under test
                self.integration.enroll_student(self.student_1, self.course)

                # check the the method tried to get the student
                mock_get_student.assert_called_once_with(
                    courseId=self.classroom_course_twin.remote_object_id,
                    userId=self.student_1.email,
                )

        # Show that, if 403 is raised, the method tries to get the up to date
        # course from the Classroom API and then tries to enroll the student again
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            # simulate a 403 error, which is raised when the enrollment code is incorrect
            mock_create.return_value.execute.side_effect = HttpError(
                resp=Mock(
                    status=403,
                    reason="",
                ),
                content=b"",
            )

            # If retrying isn't allowed, the method should raise the error
            with self.assertRaises(HttpError):
                self.integration.enroll_student(
                    self.student_1, self.course, allow_retry=False
                )

            # If retrying is allowed, the method should try to get the course again
            with patch.object(
                self.integration, "get_course_by_id"
            ) as get_course_by_id_mock:
                new_enrollment_code = "1et5x4q"
                get_course_by_id_mock.return_value = {
                    "id": "541942443924",
                    "name": "test",
                    "description": "Test description. 123 abc",
                    "enrollmentCode": new_enrollment_code,
                    "alternateLink": "https://classroom.google.com/c/NTWyNDQyNDQzOTQ3",
                }
                # simulate a 403 error, which is raised when the enrollment code is incorrect
                mock_create.return_value.execute.side_effect = HttpError(
                    resp=Mock(
                        status=403,
                        reason="",
                    ),
                    content=b"",
                )
                """
                TODO this try except is needed for now because the mock will cause the recursive call to 
                raise 403 again. Ideally, we can find a way to mock the recursive call so that it doesn't
                raise again and assert that the recursive call was made.
                """
                try:
                    self.integration.enroll_student(self.student_1, self.course)
                except:
                    pass

                # Check that the Classroom API was called to retrieve the course
                get_course_by_id_mock.assert_called_once_with(
                    self.classroom_course_twin.fallback_user,
                    self.classroom_course_twin.remote_object_id,
                )
                # Check that the enrollment code was updated
                self.assertEqual(
                    GoogleClassroomCourseTwin.objects.get(
                        pk=self.classroom_course_twin.pk
                    ).data["enrollmentCode"],
                    new_enrollment_code,
                )

    def test_get_classroom_student_submission_id_from_evo_event_participation(self):
        exam = Event.objects.create(
            course=self.course,
            **{
                "name": "exam_1",
                "event_type": Event.EXAM,
                "exercises_shown_at_a_time": None,
                "begin_timestamp": timezone.now() - timedelta(minutes=5),
                "state": Event.OPEN,
            },
        )
        coursework = {
            "id": "521084982261",
            "courseId": self.classroom_course_twin.remote_object_id,
            "scheduledTime": "null",
            "creationTime": "2023-03-24T15:38:53.797Z",
            "title": "exam_1",
            "alternateLink": "https://classroom.google.com/c/NTQxNQyNqwQzOTQ3/a/NdjxMDg4OTgsMjYz/details",
        }
        GoogleClassroomCourseWorkTwin.create_from_remote_object(
            event=exam,
            remote_object=coursework,
            remote_object_id=coursework["id"],
        )

        submission = {
            "id": "Cf3Imv_AkaoRWKJN34vqQe",
            "courseId": "541942443924",
            "courseWorkId": "521084982261",
            "userId": "229946036563518627236",
            "alternateLink": "https://classroom.google.com/c/NTQxNQyNqwQzOTQ3/a/NdjxMDg4OTgsMjYz/submissions/by-status/and-sort-last-name/student/MTk1WDI2NTU3OEUw",
        }
        participation_with_twin = EventParticipation.objects.create(
            user=self.student_2, event_id=exam.pk
        )
        twin = GoogleClassroomCourseWorkSubmissionTwin.create_from_remote_object(
            remote_object=submission,
            remote_object_id=submission["id"],
            participation=participation_with_twin,
        )

        # Check that, if a twin for the submission exists, the method returns that twin's remote_object_id
        self.assertEqual(
            self.integration.get_classroom_student_submission_id_from_evo_event_participation(
                participation_with_twin
            ),
            twin.remote_object_id,
        )

        participation_without_twin = EventParticipation.objects.create(
            user=self.student_1, event_id=exam.pk
        )

        mock_service = Mock()
        # mock the API call to retrieve a CourseWorkSubmission
        mock_list = mock_service.courses().courseWork().studentSubmissions().list

        # Show that, if the function is called on a participation that doesn't have a twin, but the student
        # does have a submission on Classroom associated to the coursework twin, it'll fetch that submission,
        # create a twin for it, and return the remote_object_id of the twin
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            mock_list.return_value.execute.return_value = {
                "studentSubmissions": [
                    {
                        "id": "Cf3Imv_AkaoRXKJH34vqQw",
                        "courseId": "541942443924",
                        "courseWorkId": "521084982261",
                        "userId": "229946033563518627231",
                        "alternateLink": "https://classroom.google.com/c/NTQxNQyNqwQzOTQ3/a/NdjxMDg4OTgsMjYz/submissions/by-status/and-sort-last-name/student/Mwx1WEI2NTU3OEUw",
                    }
                ]
            }
            # no twin prior to the call
            self.assertFalse(
                GoogleClassroomCourseWorkSubmissionTwin.objects.filter(
                    participation=participation_without_twin
                ).exists()
            )
            # Call the method and check that it returns the remote_object_id of the submission
            self.assertEqual(
                self.integration.get_classroom_student_submission_id_from_evo_event_participation(
                    participation_without_twin
                ),
                "Cf3Imv_AkaoRXKJH34vqQw",
            )
            # twin has been created
            self.assertTrue(
                GoogleClassroomCourseWorkSubmissionTwin.objects.filter(
                    participation=participation_without_twin
                ).exists()
            )

        participation = EventParticipation.objects.create(
            user=self.student_3, event_id=exam.pk
        )

        # Show that if the function is called on a participation that doesn't have a twin, and the student
        # doesn't have a submission on Classroom associated to the coursework twin and retrying is
        # not permitted, it'll return None
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            mock_list.return_value.execute.return_value = {}

            self.assertIsNone(
                self.integration.get_classroom_student_submission_id_from_evo_event_participation(
                    participation, allow_retry=False
                ),
            )
        # when a student doesn't have a submission, the API call returns an empty dict, but
        # we're checking for empty list too, just in case
        with patch.object(self.integration, "get_service") as get_service_mock:
            get_service_mock.return_value = mock_service
            mock_list.return_value.execute.return_value = {"studentSubmissions": []}

            self.assertIsNone(
                self.integration.get_classroom_student_submission_id_from_evo_event_participation(
                    participation, allow_retry=False
                ),
            )

        # Show that if the function is called on a participation that doesn't have a twin, and the student
        # doesn't have a submission on Classroom associated to the coursework twin and retrying is
        # permitted, it'll enroll the user on Classroom and then retry
        with patch.object(self.integration, "get_service") as get_service_mock:
            with patch.object(
                self.integration, "enroll_student"
            ) as enroll_student_mock:
                get_service_mock.return_value = mock_service
                mock_list.return_value.execute.return_value = {}

                # Call the method under test & check it tries to enroll the student
                self.integration.get_classroom_student_submission_id_from_evo_event_participation(
                    participation, allow_retry=True
                )
                enroll_student_mock.assert_called_once_with(
                    participation.user, participation.event.course
                )
        # same as above, but with an empty list
        with patch.object(self.integration, "get_service") as get_service_mock:
            with patch.object(
                self.integration, "enroll_student"
            ) as enroll_student_mock:
                get_service_mock.return_value = mock_service
                mock_list.return_value.execute.return_value = {"studentSubmissions": []}

                # Call the method under test & check it tries to enroll the student
                self.integration.get_classroom_student_submission_id_from_evo_event_participation(
                    participation, allow_retry=True
                )
                enroll_student_mock.assert_called_once_with(
                    participation.user, participation.event.course
                )

    def test_get_course_students(self):
        # TODO implement
        ...

    def test_is_teacher_on_classroom_course(self):
        # TODO implement
        ...

    def test_on_exam_participation_created(self):
        # TODO implement
        ...

    def test_on_exam_participation_turned_in(self):
        # TODO implement
        ...

    def test_on_exam_participation_assessment_updated(self):
        # TODO implement
        ...

    def test_on_exam_participation_assessment_published(self):
        # TODO implement
        ...

    def test_sync_exam_grades(self):
        # TODO implement
        ...

    def test_run_google_classroom_integration_method(self):
        # TODO implement
        ...

    def test_import_enrolled_student_from_twin_course(self):
        # TODO implement
        ...
