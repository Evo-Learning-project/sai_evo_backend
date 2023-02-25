from abc import ABC, abstractmethod
from courses.models import Event
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode


class BaseEvoIntegration(ABC):
    @abstractmethod
    def get_credentials(self):
        ...

    @abstractmethod
    def on_exam_published(self, user: User, exam: Event):
        ...

    @abstractmethod
    def on_lesson_published(self, user: User, lesson: LessonNode):
        ...

    @abstractmethod
    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        ...
