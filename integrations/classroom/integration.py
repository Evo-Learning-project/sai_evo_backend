from integrations.integration import BaseEvoIntegration
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode
from courses.models import Event


class GoogleClassroomIntegration(BaseEvoIntegration):
    def get_service(self):
        ...

    def get_credentials(self):
        ...

    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        ...

    def on_exam_published(self, user: User, exam: Event):
        ...

    def on_lesson_published(self, user: User, lesson: LessonNode):
        ...
