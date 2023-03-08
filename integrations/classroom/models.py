from django.db import models
from courses.models import Course

from integrations.models import RemoteTwinResource


class GoogleClassroomCourseTwin(RemoteTwinResource):
    """
    A Google Classroom course associated to a course on Evo
    """

    REMOTE_OBJECT_FIELDS = [
        "id",
        "name",
        "descriptionHeading",
        "enrollmentCode",
        "alternateLink",
    ]

    course = models.OneToOneField(Course, on_delete=models.CASCADE)

    # whether the integration is currently enabled
    enabled = models.BooleanField(default=True, blank=False, null=False)

    def __str__(self):
        return f"{str(self.course)} - {self.data.get('name')} ({self.remote_object_id})"
