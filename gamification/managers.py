from django.db import models

from gamification.querysets import GoalLevelQuerySet, GamificationContextQuerySet


class GoalLevelManager(models.Manager):
    def get_queryset(self):
        return GoalLevelQuerySet(self.model, using=self._db)


class GamificationContextManager(models.Manager):
    def get_queryset(self):
        return GamificationContextQuerySet(self.model, using=self._db)
