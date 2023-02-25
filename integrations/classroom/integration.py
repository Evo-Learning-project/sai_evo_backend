from integrations.integration import BaseEvoIntegration
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode
from courses.models import Event

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleClassroomIntegration(BaseEvoIntegration):
    SCOPES = [
        "https://www.googleapis.com/auth/classroom.courses.readonly",
        "https://www.googleapis.com/auth/classroom.announcements",
        "https://www.googleapis.com/auth/classroom.courseworkmaterials",
        "https://www.googleapis.com/auth/classroom.coursework.students",
    ]

    def get_service(self):
        creds = self.get_credentials()
        return build("classroom", "v1", credentials=creds)

    def get_credentials(self):
        ...

    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        ...

    def on_exam_published(self, user: User, exam: Event):
        ...

    def on_lesson_published(self, user: User, lesson: LessonNode):
        ...
