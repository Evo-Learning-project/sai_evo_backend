from django.db import models

from gamification.querysets import GoalLevelQuerySet


class GoalLevelManager(models.Manager):
    def get_queryset(self):
        return GoalLevelQuerySet(self.model, using=self._db)
