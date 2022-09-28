from django.db import models
from users.models import User
from .logic import is_demo_mode


class DemoCoursesQuerySet(models.QuerySet):
    def available_in_demo_mode_to(self, user: User):
        return self.exclude(pk__in=[7, 8])
