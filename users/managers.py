from django.db import models

from users.querysets import UserQuerySet


class UserManager(models.Manager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)
