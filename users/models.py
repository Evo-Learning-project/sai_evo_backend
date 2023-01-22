from django.contrib.auth.models import AbstractUser
from django.db import models
from demo_mode.logic import is_demo_mode

from users.managers import UserManager


TEACHER_EMAIL_DOMAINS = ["unipi.it"]


class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    roles = models.ManyToManyField(
        "courses.CourseRole",
        related_name="users",
        blank=True,
    )
    mat = models.CharField(max_length=6, blank=True)
    course = models.CharField(max_length=1, blank=True)
    avatar_url = models.TextField(blank=True)

    objects = UserManager()

    if is_demo_mode():
        from demo_mode.models import DemoUserManager

        objects = DemoUserManager()

    def __str__(self):
        return self.username + " - " + self.full_name

    def save(self, *args, **kwargs):
        creating = self.pk is None

        super(User, self).save(*args, **kwargs)

        if (
            len(self.email) > 0
            and creating
            and self.email.split("@")[1] in TEACHER_EMAIL_DOMAINS
        ):
            self.is_teacher = True
            self.save()

    @property
    def full_name(self):
        if len(self.first_name) == 0 and len(self.last_name) == 0:
            return self.email

        return " ".join(
            [
                t.capitalize()
                for t in (self.first_name + " " + self.last_name).split(" ")
            ]
        )
