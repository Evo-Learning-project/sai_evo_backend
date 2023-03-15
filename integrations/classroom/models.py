from django.db import models
from courses.models import Course

from integrations.models import RemoteTwinResource
from users.models import User


class GoogleClassroomCourseTwin(RemoteTwinResource):
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
    fallback_user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{str(self.course)} - {self.data.get('name')} ({self.remote_object_id})"
