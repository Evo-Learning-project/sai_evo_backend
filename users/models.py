from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    roles = models.ManyToManyField("courses.CourseRole", blank=True)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super(User, self).save(*args, **kwargs)
        if len(self.email) > 0 and creating and self.email.split("@")[1] == "unipi.it":
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
