from integrations.classroom.factories import get_assignment_payload
from integrations.classroom import messages

from integrations.exceptions import MissingIntegrationParameters
from integrations.integration import BaseEvoIntegration
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode
from courses.models import Event, Course

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os

import environ


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
        # TODO implement
        ...

    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        ...

    def on_exam_published(self, user: User, exam: Event):
        print("on_exam_published")
        course_id = self.get_classroom_course_id_from_evo_course(exam.course)
        service = self.get_service(user)
        exam_url = exam.get_absolute_url()
        coursework_payload = get_assignment_payload(
            title=exam.name,
            description=messages.EXAM_PUBLISHED,
            exam_url=exam_url,
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
        print(results)

    def on_lesson_published(self, user: User, lesson: LessonNode):
        ...

    def get_courses_taught_by(self, user: User):
        ...

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

    def get_course_teachers(self, course: Course):
        ...
