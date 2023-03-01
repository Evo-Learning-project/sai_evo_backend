from django.db import models
from courses.models import Course

from integrations.models import RemoteTwinResource


class GoogleClassroomCourseTwin(RemoteTwinResource):
    """
    A Google Classroom course associated to a course on Evo
    """

    course = models.OneToOneField(Course, on_delete=models.CASCADE)
