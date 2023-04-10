from django.db import models
from course_tree.models import AnnouncementNode, LessonNode
from courses.models import Course, Event, EventParticipation, UserCourseEnrollment

from integrations.models import RemoteTwinResource
from users.models import User

from django_lifecycle import (
    LifecycleModelMixin,
    hook,
    AFTER_CREATE,
)


class GoogleClassroomIntegrationFailedTask(models.Model):
    """
    Represents a failed task that was triggered by the Classroom integration.
    It's used to keep track of failed tasks so that they can be notified to the user
    and possibly retried.
    """

    task_id = models.CharField(max_length=255)
    # related to the type of exception that was raised
    error_kind = models.CharField(max_length=255, blank=True)


class GoogleClassroomCourseTwin(LifecycleModelMixin, RemoteTwinResource):
    """
    A Google Classroom course associated to a course on Evo
    """

    REMOTE_OBJECT_FIELDS = [
        "id",
        "name",
        "description",
        "enrollmentCode",
        "alternateLink",
    ]

    course = models.OneToOneField(Course, on_delete=models.CASCADE)

    # whether the integration is currently enabled
    enabled = models.BooleanField(default=True, blank=False, null=False)

    # a user who at the time of the creation of this integration was a teacher on the
    # selected Classroom course. this ensures that, whenever a user performs an action
    # that requires creating or modifying content on Classroom,  even if that user doesn't
    # have teacher permissions on the Classroom course, there will be at least one user
    # that can be used to perform the action via the Classroom API
    # TODO find a way to handle the fallback_user not being a teacher on classroom anymore. e.g. in the integration view have "health" analytics about the integration & provide ways to fix issues
    fallback_user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{str(self.course)} - {self.data.get('name')} ({self.remote_object_id})"

    @hook(AFTER_CREATE)
    def on_create(self):
        from integrations.classroom.controller import (
            GoogleClassroomIntegrationController,
        )

        # when a new Google Classroom course twin is created, enroll all students
        # in the corresponding course to the paired Classroom course
        GoogleClassroomIntegrationController().sync_enrolled_students(self.course)


class GoogleClassroomCourseWorkTwin(RemoteTwinResource):
    REMOTE_OBJECT_FIELDS = [
        "id",
        "courseId",
        "scheduledTime",
        "creationTime",
        "title",
        "description",
        "alternateLink",
    ]

    event = models.OneToOneField(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f"{str(self.event)} - ({self.remote_object_id})"


class GoogleClassroomAnnouncementTwin(RemoteTwinResource):
    REMOTE_OBJECT_FIELDS = [
        "id",
        "courseId",
        "alternateLink",
        "text",
        "creationTime",
        "updateTime",
    ]

    announcement = models.OneToOneField(AnnouncementNode, on_delete=models.CASCADE)

    def __str__(self):
        return f"{str(self.announcement)} - ({self.remote_object_id})"


class GoogleClassroomMaterialTwin(RemoteTwinResource):
    REMOTE_OBJECT_FIELDS = [
        "id",
        "courseId",
        "alternateLink",
        "title",
        "description",
        "state",
        "creationTime",
        "updateTime",
    ]

    lesson = models.OneToOneField(LessonNode, on_delete=models.CASCADE)

    def __str__(self):
        return f"{str(self.lesson)} - ({self.remote_object_id})"


class GoogleClassroomEnrollmentTwin(RemoteTwinResource):
    REMOTE_OBJECT_FIELDS = [
        "courseId",
        "userId",
        "profile",
    ]

    enrollment = models.OneToOneField(UserCourseEnrollment, on_delete=models.CASCADE)

    def __str__(self):
        return f"{str(self.enrollment)} - ({self.remote_object_id})"


class GoogleClassroomCourseWorkSubmissionTwin(RemoteTwinResource):
    REMOTE_OBJECT_FIELDS = [
        "id",
        "courseId",
        "courseWorkId",
        "userId",
        "alternateLink",
    ]

    participation = models.OneToOneField(EventParticipation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{str(self.participation)} - ({self.remote_object_id})"
