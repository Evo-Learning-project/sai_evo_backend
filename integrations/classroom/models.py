from django.db import models
from courses.models import Course

from integrations.models import RemoteTwinResource


class GoogleClassroomCourseTwin(RemoteTwinResource):
    """
    A Google Classroom course associated to a course on Evo
    """

    REMOTE_OBJECT_FIELDS = [
        "name",
        "descriptionHeading",
        "enrollmentCode",
        "alternateLink",
    ]

    course = models.OneToOneField(Course, on_delete=models.CASCADE)

    def __str__(self):
        return f"{str(self.course)} - {self.data.get('name')} ({self.remote_object_id})"