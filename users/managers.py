from django.db import models

from users.querysets import UserQuerySet

from django.contrib.auth.models import UserManager


class UserManager(UserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)
