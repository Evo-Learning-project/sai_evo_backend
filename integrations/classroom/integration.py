from typing import Optional
from integrations.classroom.exceptions import (
    DomainSettingsError,
    CannotEnrollTeacher,
    InvalidGoogleOAuth2Credentials,
    MissingGoogleOAuth2Credentials,
)
from integrations.classroom.factories import (
    get_announcement_payload,
    get_assignment_payload,
    get_material_payload,
)
from integrations.classroom import messages
from integrations.classroom.models import (
    GoogleClassroomAnnouncementTwin,
    GoogleClassroomCourseTwin,
    GoogleClassroomCourseWorkSubmissionTwin,
    GoogleClassroomCourseWorkTwin,
    GoogleClassroomEnrollmentTwin,
    GoogleClassroomMaterialTwin,
)

from integrations.exceptions import MissingIntegrationParameters
from integrations.integration import BaseEvoIntegration
from integrations.models import GoogleOAuth2Credentials
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode
from courses.models import Event, Course, EventParticipation, UserCourseEnrollment

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from django.db import IntegrityError

from google.auth.exceptions import RefreshError


import os

import environ

import logging

logger = logging.getLogger(__name__)


class GoogleClassroomIntegration(BaseEvoIntegration):
    STUDENT_SCOPES = [
        "https://www.googleapis.com/auth/classroom.rosters",
        "https://www.googleapis.com/auth/classroom.coursework.me",
    ]
    TEACHER_SCOPES = [
        "https://www.googleapis.com/auth/classroom.courses.readonly",
        "https://www.googleapis.com/auth/classroom.announcements",
        "https://www.googleapis.com/auth/classroom.courseworkmaterials",
        "https://www.googleapis.com/auth/classroom.coursework.students",
        "https://www.googleapis.com/auth/classroom.rosters",
        "https://www.googleapis.com/auth/classroom.profile.emails",
        "https://www.googleapis.com/auth/classroom.coursework.me",
    ]

    def get_client_config(self):
        env = environ.Env()

        client_id = os.environ.get("GOOGLE_INTEGRATION_CLIENT_ID")
        project_id = os.environ.get("GOOGLE_INTEGRATION_PROJECT_ID")
        client_secret = os.environ.get("GOOGLE_INTEGRATION_CLIENT_SECRET")
        redirect_uris = env.list(
            "GOOGLE_CLASSROOM_INTEGRATION_REDIRECT_URIS", default=[]
        )

        if any(c is None for c in (client_id, project_id, client_secret)):
            raise MissingIntegrationParameters(
                "Missing parameters for Google Classroom integration"
            )

        return {
            "installed": {
                "client_id": client_id,
                "project_id": project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": redirect_uris,
            }
        }

    """
    Getters
    """

    def get_domain_administrator_user(self) -> Optional[User]:
        # TODO implement
        return None

    def get_user_for_action(self, course: Course, user: User):
        """
        If the user supplied via the `user` parameter is suitable to perform
        an action on Classroom (i.e. it has teacher permissions for the course
        associated to `course`), then `user` is returned. Otherwise, the fallback
        user referenced by the GoogleClassroomCourseTwin instance associated to
        `course` is returned.

        TODO this currently always returns the fallback_user
        """
        return GoogleClassroomCourseTwin.objects.get(course=course).fallback_user

    def get_classroom_course_id_from_evo_course(self, course: Course):
        return GoogleClassroomCourseTwin.objects.get(course=course).remote_object_id

    def get_classroom_course_from_evo_course(self, course: Course):
        return GoogleClassroomCourseTwin.objects.get(course=course)

    def get_classroom_coursework_id_from_evo_exam(self, exam: Event):
        return GoogleClassroomCourseWorkTwin.objects.get(event=exam).remote_object_id

    def get_classroom_student_submission_id_from_evo_event_participation(
        self, participation: EventParticipation, allow_retry: bool = True
    ):
        try:
            return GoogleClassroomCourseWorkSubmissionTwin.objects.get(
                participation=participation
            ).remote_object_id
        except GoogleClassroomCourseWorkSubmissionTwin.DoesNotExist:
            # retrieve the submission from Classroom & create twin model
            course = participation.event.course
            classroom_course = self.get_classroom_course_from_evo_course(course)
            course_id = classroom_course.remote_object_id

            coursework_id = self.get_classroom_coursework_id_from_evo_exam(
                participation.event
            )

            # we use the fallback user to handle edge cases where the student hasn't
            # granted access to their Classroom data
            user = classroom_course.fallback_user
            service = self.get_service(user)

            try:
                response = (
                    service.courses()
                    .courseWork()
                    .studentSubmissions()
                    .list(
                        courseId=course_id,
                        courseWorkId=coursework_id,
                        userId=participation.user.email,
                    )
                    .execute()
                )
            except HttpError as error:
                logger.error(
                    f"Error during on_exam_participation_created with participation {participation.pk}",
                    exc_info=error,
                )
                raise

            if (
                "studentSubmissions" in response
                and len(response["studentSubmissions"]) > 0
            ):
                submission = response["studentSubmissions"][0]
                twin = (
                    GoogleClassroomCourseWorkSubmissionTwin.create_from_remote_object(
                        participation=participation,
                        remote_object_id=submission["id"],
                        remote_object=submission,
                    )
                )
                return twin.remote_object_id

            logger.warning(
                f"Could not find submission for participation "
                f"{participation.pk}, response was {response}"
            )
            if allow_retry:
                try:
                    self.enroll_student(participation.user, course)
                except CannotEnrollTeacher:
                    return None
                except Exception as e:
                    logger.error(
                        f"Error while trying to enroll student {participation.user.pk} "
                        f"in course {course_id}",
                        exc_info=e,
                    )
                    raise
                # retry
                return self.get_classroom_student_submission_id_from_evo_event_participation(
                    participation, False
                )
            else:
                return None

    def get_service(self, user: User):
        creds = self.get_credentials(user)
        return build("classroom", "v1", credentials=creds)

    def get_credentials(self, user: User):
        try:
            credentials_model_instance = GoogleOAuth2Credentials.objects.get(user=user)
        except GoogleOAuth2Credentials.DoesNotExist:
            raise MissingGoogleOAuth2Credentials

        client_config = self.get_client_config()["installed"]

        # dict taking user's access token, refresh token, and client information used
        # to construct a Credentials object
        authorized_user_info = {
            "token": credentials_model_instance.access_token,
            "refresh_token": credentials_model_instance.refresh_token,
            "scopes": credentials_model_instance.scope,
            **{
                key: client_config[key]
                for key in ("client_id", "client_secret", "token_uri")
            },
        }

        creds = Credentials.from_authorized_user_info(authorized_user_info)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError as error:
                    logger.error(
                        f"Unable to refresh credentials for user {user.pk}",
                        exc_info=error,
                    )
                    # delete credentials model instance as it's invalid
                    credentials_model_instance.delete()
                    raise InvalidGoogleOAuth2Credentials
                # save new token to credentials model instance
                credentials_model_instance.update_access_token(creds.token)
            else:
                # credentials are invalid for some reason and we cannot refresh
                logger.error(f"Unable to refresh credentials for user {user.pk}")
                # delete credentials model instance as it's invalid
                credentials_model_instance.delete()
                raise InvalidGoogleOAuth2Credentials

        # ensure we're storing the latest scope
        credentials_model_instance.update_scope_if_changed(creds.granted_scopes)

        return creds

    """
    Event handlers
    """

    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        course = announcement.get_course()
        course_id = self.get_classroom_course_id_from_evo_course(course)
        action_user = self.get_user_for_action(course, user)

        service = self.get_service(action_user)

        announcement_url = announcement.get_absolute_url()
        announcement_payload = get_announcement_payload(
            text=announcement.body, announcement_url=announcement_url
        )
        if not GoogleClassroomAnnouncementTwin.objects.filter(
            announcement=announcement
        ).exists():
            classroom_announcement = (
                service.courses()
                .announcements()
                .create(courseId=course_id, body=announcement_payload)
                .execute()
            )
            twin = GoogleClassroomAnnouncementTwin.create_from_remote_object(
                announcement=announcement,
                remote_object_id=classroom_announcement["id"],
                remote_object=classroom_announcement,
            )
            return twin
        else:
            logger.warning(
                f"Announcement {str(announcement.pk)} was published but it already has a twin"
            )

    def on_exam_published(self, user: User, exam: Event):
        course = exam.course
        course_id = self.get_classroom_course_id_from_evo_course(course)
        action_user = self.get_user_for_action(course, user)

        service = self.get_service(action_user)

        # if the exam doesn't have a twin resource on Classroom yet, create one
        if not GoogleClassroomCourseWorkTwin.objects.filter(event=exam).exists():
            exam_url = exam.get_absolute_url()
            coursework_payload = get_assignment_payload(
                title=exam.name,
                description=messages.EXAM_PUBLISHED,
                exam_url=exam_url,
                scheduled_timestamp=exam.begin_timestamp,
                # TODO we might need to make sure this value is correct when the exam begins (i.e. update it if changed)
                max_score=exam.max_score,
            )

            coursework = (
                service.courses()
                .courseWork()
                .create(
                    courseId=course_id,
                    body=coursework_payload,
                )
                .execute()
            )
            twin = GoogleClassroomCourseWorkTwin.create_from_remote_object(
                event=exam,
                remote_object_id=coursework["id"],
                remote_object=coursework,
            )
            return twin
        else:
            logger.warning(
                f"Exam {str(exam.pk)} was published but it already has a twin"
            )

    def on_exam_participation_created(self, participation: EventParticipation):
        classroom_course = self.get_classroom_course_from_evo_course(
            participation.event.course
        )
        course_id = classroom_course.remote_object_id
        coursework_id = self.get_classroom_coursework_id_from_evo_exam(
            participation.event
        )

        service = self.get_service(classroom_course.fallback_user)

        submission_id = (
            self.get_classroom_student_submission_id_from_evo_event_participation(
                participation
            )
        )

        if submission_id is None:
            # this should only happen if the user is a teacher in the classroom course
            logger.debug(
                f"get_classroom_student_submission_id_from_evo_event_participation \
                    returned None in on_exam_participation_created with pk {participation.pk}"
            )
            return

        # TODO will error with 400 if submission has already been turned in - but this shouldn't happen
        # add a URL attachment to the existing student submission linking to
        # the corresponding EventParticipation object
        # TODO error handling
        (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .modifyAttachments(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=submission_id,
                body={
                    "addAttachments": [
                        {"link": {"url": participation.get_absolute_url()}}
                    ]
                },
            )
            .execute()
        )

    def on_exam_participation_turned_in(self, participation: EventParticipation):
        classroom_course = self.get_classroom_course_from_evo_course(
            participation.event.course
        )

        service = self.get_service(participation.user)

        course_id = classroom_course.remote_object_id
        coursework_id = self.get_classroom_coursework_id_from_evo_exam(
            participation.event
        )

        submission_id = (
            self.get_classroom_student_submission_id_from_evo_event_participation(
                participation
            )
        )

        if submission_id is None:
            # this should only happen if the user is a teacher in the classroom course
            logger.debug(
                f"get_classroom_student_submission_id_from_evo_event_participation \
                    returned None in on_exam_participation_turned_in with pk {participation.pk}"
            )
            return

        (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .turnIn(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=submission_id,
            )
            .execute()
        )

    def on_exam_participation_assessment_updated(
        self, participation: EventParticipation
    ):
        classroom_course = self.get_classroom_course_from_evo_course(
            participation.event.course
        )

        service = self.get_service(classroom_course.fallback_user)

        course_id = classroom_course.remote_object_id
        coursework_id = self.get_classroom_coursework_id_from_evo_exam(
            participation.event
        )

        submission_id = (
            self.get_classroom_student_submission_id_from_evo_event_participation(
                participation
            )
        )

        if submission_id is None:
            # this should only happen if the user is a teacher in the classroom course
            return

        (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .patch(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=submission_id,
                updateMask="draftGrade",
                # TODO ensure score is a number
                body={
                    "draftGrade": participation.score,
                },
            )
            .execute()
        )

    def on_exam_participation_assessment_published(
        self, participation: EventParticipation
    ):
        classroom_course = self.get_classroom_course_from_evo_course(
            participation.event.course
        )

        service = self.get_service(classroom_course.fallback_user)

        course_id = classroom_course.remote_object_id
        coursework_id = self.get_classroom_coursework_id_from_evo_exam(
            participation.event
        )

        submission_id = (
            self.get_classroom_student_submission_id_from_evo_event_participation(
                participation
            )
        )

        if submission_id is None:
            # this should only happen if the user is a teacher in the classroom course
            return

        patched_submission = (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .patch(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=submission_id,
                updateMask="assignedGrade,draftGrade",
                # TODO ensure score is a number
                body={
                    "assignedGrade": participation.score,
                    "draftGrade": participation.score,
                },
            )
            .execute()
        )

        if patched_submission["state"] == "TURNED_IN":
            # if the submission had been turned in, return it - if we try to return
            # a submission that hasn't been turned in, we'll get a 400 error
            (
                service.courses()
                .courseWork()
                .studentSubmissions()
                .return_(
                    courseId=course_id,
                    courseWorkId=coursework_id,
                    id=submission_id,
                )
                .execute()
            )

    def on_lesson_published(self, user: User, lesson: LessonNode):
        course = lesson.get_course()
        course_id = self.get_classroom_course_id_from_evo_course(course)

        action_user = self.get_user_for_action(course, user)

        service = self.get_service(action_user)

        lesson_url = lesson.get_absolute_url()
        coursework_payload = get_material_payload(
            title=lesson.title,
            description=messages.VIEW_LESSON_ON_EVO,
            material_url=lesson_url,
        )
        # if the lesson doesn't have a twin resource on Classroom yet, create one
        if not GoogleClassroomMaterialTwin.objects.filter(lesson=lesson).exists():
            # in the future we may also take into consideration topics
            # see: https://developers.google.com/classroom/reference/rest/v1/courses.topics
            material = (
                service.courses()
                .courseWorkMaterials()
                .create(
                    courseId=course_id,
                    body=coursework_payload,
                )
                .execute()
            )
            twin = GoogleClassroomMaterialTwin.create_from_remote_object(
                lesson=lesson,
                remote_object_id=material["id"],
                remote_object=material,
            )
            return twin
        else:
            logger.warning(
                f"Lesson {str(lesson.pk)} was published but it already has a twin"
            )

    def on_student_enrolled(self, enrollment: UserCourseEnrollment):
        # we need to use the student's credentials for enrollment. in the future, it could
        # be taken into consideration to use the credentials of a domain administrator
        # see https://developers.google.com/classroom/reference/rest/v1/courses.students/create
        user = enrollment.user
        course = enrollment.course

        try:
            classroom_enrollment = self.enroll_student(user, course)
        except CannotEnrollTeacher:
            return

        # create the twin, if it doesn't exist yet
        try:
            GoogleClassroomEnrollmentTwin.create_from_remote_object(
                enrollment=enrollment, remote_object=classroom_enrollment
            )
        except IntegrityError:
            # twin already exists
            pass

    def enroll_student(self, user: User, course: Course, allow_retry: bool = True):
        classroom_course = self.get_classroom_course_from_evo_course(course)
        course_id = classroom_course.remote_object_id

        try:
            service = self.get_service(user)
        except (MissingGoogleOAuth2Credentials, InvalidGoogleOAuth2Credentials):
            # if the user doesn't have valid credentials, try
            # to use the domain administrator's credentials
            domain_administrator = self.get_domain_administrator_user()
            if domain_administrator is None:
                raise
            logging.warning(
                f"User {user.pk} doesn't have valid credentials, "
                "falling back to domain administrator's"
            )
            service = self.get_service(classroom_course.fallback_user)

        # enrollment code is required to enroll student
        enrollment_code = classroom_course.data["enrollmentCode"]

        try:
            classroom_enrollment = (
                service.courses()
                .students()
                .create(
                    courseId=course_id,
                    enrollmentCode=enrollment_code,
                    body={"userId": user.email},
                )
                .execute()
            )
        except HttpError as error:
            status = error.status_code

            # error 409 means the student is already enrolled on Classroom
            # see https://developers.google.com/classroom/reference/rest/v1/courses.students/create
            if status == 409:
                # this means the student had already enrolled on Classroom before they did on Evo
                # or the user is a teacher in the Classroom course: if the user is a teacher,
                # we can't enroll them as a student, so we raise an exception to signal that,
                # otherwise we retrieve the enrollment from Classroom and return it
                if self.is_teacher_on_classroom_course(user, course):
                    raise CannotEnrollTeacher

                # retrieve the existing enrollment from Classroom
                classroom_enrollment = (
                    service.courses()
                    .students()
                    .get(courseId=course_id, userId=user.email)
                    .execute()
                )
            # error 403 may be returned because the enrollmentCode used is invalid.
            # try to get the up-to-date enrollmentCode and retry the request
            elif status == 403:
                if not allow_retry:
                    raise
                up_to_date_classroom_course = self.get_course_by_id(
                    classroom_course.fallback_user, classroom_course.remote_object_id
                )
                classroom_course.update_from_remote_object(up_to_date_classroom_course)
                # retry the request with the new enrollmentCode
                return self.enroll_student(user, course, allow_retry=False)
            elif status == 400 and error.reason.startswith("@DomainSettingsError"):
                # the student has an email address whose domain is not allowed to be enrolled
                # we can't do anything about it, so we raise an unrecoverable exception
                logger.error(f"Domain error in enrolling student {user.pk}")
                raise DomainSettingsError
            else:
                logger.error(
                    f"Error during on_student_enrolled for user {user.pk} and course {course.pk}",
                    exc_info=error,
                )
                raise

        return classroom_enrollment

    """
    Utility
    """

    def is_teacher_on_classroom_course(self, user: User, course: Course):
        classroom_course = self.get_classroom_course_from_evo_course(course)
        course_id = classroom_course.remote_object_id
        service = self.get_service(classroom_course.fallback_user)
        try:
            service.courses().teachers().get(
                courseId=course_id, userId=user.email
            ).execute()
            return True
        except:
            return False

    def get_courses_taught_by(self, user: User):
        """
        Returns a list of Classroom courses that the requesting user is a teacher of.
        The fields returned for those courses are the course id plus the fields included
        in `GoogleClassroomCourseTwin.REMOTE_OBJECT_FIELDS`
        """
        service = self.get_service(user)
        teacher_id = "me"  # shorthand for current user
        courses = (
            service.courses().list(teacherId=teacher_id).execute().get("courses", [])
        )
        return [
            {f: c.get(f) for f in GoogleClassroomCourseTwin.REMOTE_OBJECT_FIELDS}
            for c in courses
        ]

    def get_course_students(self, course: Course):
        """
        Returns the list of students enrolled in the Classroom course
        corresponding to the Course object passed as argument
        """
        course_id = self.get_classroom_course_id_from_evo_course(course)
        service = self.get_service(course.creator)

        ret = []

        first_request = True
        next_page_token = None

        # iterate as long as you get a next-page token in the response
        while first_request or next_page_token:
            first_request = False
            # fetch next page
            response = (
                service.courses()
                .students()
                .list(courseId=course_id, pageToken=next_page_token)
                .execute()
            )
            # TODO error handling
            next_page_token = response.get("nextPageToken")
            students = response["students"]
            ret.extend(
                [
                    {
                        "email": s["profile"]["emailAddress"],
                        "first_name": s["profile"].get("name", {}).get("givenName", ""),
                        "last_name": s["profile"].get("name", {}).get("familyName", ""),
                    }
                    for s in students
                ]
            )

        return ret

    def get_course_by_id(self, user: User, course_id: str):
        service = self.get_service(user)
        return service.courses().get(id=course_id).execute()

    def get_course_teachers(self, course: Course):
        ...
