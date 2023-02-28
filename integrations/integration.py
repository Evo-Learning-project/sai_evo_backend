from abc import ABC, abstractmethod
from courses.models import Event, EventParticipation
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode


class BaseEvoIntegration(ABC):
    @abstractmethod
    def get_credentials(self, user: User):
        ...

    @abstractmethod
    def on_exam_published(self, user: User, exam: Event):
        ...

    @abstractmethod
    def on_exam_participation_created(self, participation: EventParticipation):
        ...

    @abstractmethod
    def on_exam_participation_turned_in(self, participation: EventParticipation):
        ...

    @abstractmethod
    def on_lesson_published(self, user: User, lesson: LessonNode):
        ...

    @abstractmethod
    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        ...
