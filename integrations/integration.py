from abc import ABC, abstractmethod
from courses.models import Course, Event, EventParticipation, UserCourseEnrollment
from users.models import User
from course_tree.models import AnnouncementNode, LessonNode

import inspect


class BaseEvoIntegration(ABC):
    ACTION_HANDLER_PREFIX = "on_"

    @classmethod
    def get_available_actions(cls):
        """
        Returns a list of actions that the integration is able to handle.
        The actions can be handled by calling a method named "on_" + name of the action
        on the handler class
        """
        ret = []
        for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith(cls.ACTION_HANDLER_PREFIX):
                ret.append(name[len(cls.ACTION_HANDLER_PREFIX) :])
        return ret

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
    def on_exam_participation_assessment_published(
        self, participation: EventParticipation
    ):
        ...

    @abstractmethod
    def on_lesson_published(self, user: User, lesson: LessonNode):
        ...

    @abstractmethod
    def on_announcement_published(self, user: User, announcement: AnnouncementNode):
        ...

    @abstractmethod
    def on_student_enrolled(self, enrollment: UserCourseEnrollment):
        ...
