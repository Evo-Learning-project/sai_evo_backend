from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)

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

    def has_teacher_privileges(self, course):
        # TODO stub
        return self.is_teacher

    def can_participate(self, event):
        # TODO stub
        return True

    def can_update_participation(self, participation):
        from courses.models import Event

        # TODO stub
        return not participation.event.state == Event.CLOSED


class CoursePermission(models.Model):
    # TODO implement
    # can add exercises, can edit/delete exercises, can create events, can edit/delete events
    # can assess submissions, can publish assessments, can create/edit/delete announcements
    # also have a special __all__ permission
    pass
