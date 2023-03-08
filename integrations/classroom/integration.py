from integrations.classroom.exceptions import (
    InvalidGoogleOAuth2Credentials,
    MissingGoogleOAuth2Credentials,
)
from integrations.classroom.factories import (
    get_announcement_payload,
    get_assignment_payload,
    get_material_payload,
)
from integrations.classroom import messages
from integrations.classroom.models import GoogleClassroomCourseTwin

from integrations.exceptions import MissingIntegrationParameters
from integrations.integration import BaseEvoIntegration
from integrations.models import GoogleOAuth2Credentials
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode
from courses.models import Event, Course, EventParticipation

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os

import environ

import logging

logger = logging.getLogger(__name__)


class GoogleClassroomIntegration(BaseEvoIntegration):
    SCOPES = [
        "https://www.googleapis.com/auth/classroom.courses.readonly",
        "https://www.googleapis.com/auth/classroom.announcements",
        "https://www.googleapis.com/auth/classroom.courseworkmaterials",
        "https://www.googleapis.com/auth/classroom.coursework.students",
        "https://www.googleapis.com/auth/classroom.rosters",
        "https://www.googleapis.com/auth/classroom.profile.emails",
    ]

    def get_classroom_course_id_from_evo_course(self, course: Course):
        return "541442443947"

    def get_classroom_coursework_id_from_evo_exam(self, exam: Event):
        return "543007020813"

    def get_classroom_student_submission_id_from_evo_event_participation(
        self, participation: EventParticipation
    ):
        return "Cg4Imv_AkaoREI2u9u3mDw"

    def get_client_config(self):
        env = environ.Env()

        client_id = os.environ.get("GOOGLE_CLASSROOM_INTEGRATION_CLIENT_ID")
        project_id = os.environ.get("GOOGLE_CLASSROOM_INTEGRATION_PROJECT_ID")
        client_secret = os.environ.get("GOOGLE_CLASSROOM_INTEGRATION_CLIENT_SECRET")
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
                creds.refresh(Request())
                # save new token to credentials model instance
                credentials_model_instance.access_token = creds.token
                credentials_model_instance.save()
            else:
                # credentials are invalid for some reason and we cannot refresh
                logger.critical(
                    "Unable to refresh credentials for user " + str(user.pk)
                )
                raise InvalidGoogleOAuth2Credentials

        return creds

    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        course_id = self.get_classroom_course_id_from_evo_course(
            announcement.get_course()
        )
        service = self.get_service(user)
        announcement_url = announcement.get_absolute_url()
        announcement_payload = get_announcement_payload(
            text=announcement.body, announcement_url=announcement_url
        )
        results = (
            service.courses()
            .announcements()
            .create(courseId=course_id, body=announcement_payload)
            .execute()
        )
        # TODO handle errors
        # TODO create integration object
        return results

    def on_exam_published(self, user: User, exam: Event):
        course_id = self.get_classroom_course_id_from_evo_course(exam.course)
        service = self.get_service(user)
        exam_url = exam.get_absolute_url()
        coursework_payload = get_assignment_payload(
            title=exam.name,
            description=messages.EXAM_PUBLISHED,
            exam_url=exam_url,
            scheduled_timestamp=exam.begin_timestamp.isoformat(),
        )
        results = (
            service.courses()
            .courseWork()
            .create(
                courseId=course_id,
                body=coursework_payload,
            )
            .execute()
        )
        # TODO handle errors
        # TODO create integration object
        return results

    def on_exam_participation_created(self, participation: EventParticipation):
        service = self.get_service(participation.user)

        course_id = self.get_classroom_course_id_from_evo_course(
            participation.event.course
        )
        exam_id = self.get_classroom_coursework_id_from_evo_exam(participation.event)
        submission_id = (
            self.get_classroom_student_submission_id_from_evo_event_participation(
                participation
            )
        )

        # add a URL attachment to the existing student submission linking to
        # the corresponding EventParticipation object
        (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .modifyAttachments(
                courseId=course_id,
                courseWorkId=exam_id,
                id=submission_id,
                body={
                    "addAttachments": [
                        {"link": {"url": participation.get_absolute_url()}}
                    ]
                },
            )
            .execute()
        )
        # TODO error handling

    def on_exam_participation_turned_in(self, participation: EventParticipation):
        # TODO implement - turn in corresponding submission to coursework
        ...

    def on_lesson_published(self, user: User, lesson: LessonNode):
        course_id = self.get_classroom_course_id_from_evo_course(lesson.get_course())
        service = self.get_service(user)
        lesson_url = lesson.get_absolute_url()

        coursework_payload = get_material_payload(
            title=lesson.title,
            description=messages.VIEW_LESSON_ON_EVO,
            material_url=lesson_url,
        )
        # TODO handle topics - https://developers.google.com/classroom/reference/rest/v1/courses.topics
        results = (
            service.courses()
            .courseWorkMaterials()
            .create(
                courseId=course_id,
                body=coursework_payload,
            )
            .execute()
        )
        # TODO handle errors
        # TODO create integration object
        return results

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
