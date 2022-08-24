from django.db import models
from gamification.actions import VALID_ACTIONS
from users.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from courses.models import TimestampableModel


class GamificationContext(models.Model):
    """
    A gamification context is used to scope gamification-related events to a specific
    model instance, i.e. the context; this object is usually a Course.

    This allows to have scoped user scores, leaderboards, badges, etc.
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField()
    content_object = GenericForeignKey("content_type", "object_id")
    # specifies whether this is the default context for content_object,
    # i.e. the one used by actions that don't explicitly specify a context
    is_default_context = models.BooleanField(default=False)

    # TODO should context be recursive?


class Goal(models.Model):
    """
    A goal made up of one or more levels.

    Users gain points and badges when reaching goals.
    """

    context = models.ForeignKey(
        GamificationContext,
        related_name="goals",
        on_delete=models.CASCADE,
    )
    name = models.TextField()  # TODO language awareness

    # TODO have a manager that allows to create never-ending goals, e.g. with lazily generated new levels


class GoalLevel(models.Model):
    goal = models.ForeignKey(
        Goal,
        related_name="levels",
        on_delete=models.CASCADE,
    )
    # dict where keys are gamification actions and values are integers
    # representing the amount of times the action must be performed
    # in order to satisfy that requirement
    requirements = models.JSONField(default=dict, blank=False)

    level_value = models.PositiveIntegerField()
    points_awarded = models.PositiveIntegerField()
    badges_awarded = models.ManyToManyField(
        "BadgeDefinition",
        related_name="awarded_in_goal_levels",
        blank=True,
    )

    # TODO validate requirements


class ActionDefinition(models.Model):
    """
    An action that can be done by a user in a specific context
    """

    ACTIONS = [(k, v) for k, v in VALID_ACTIONS.items()]

    context = models.ForeignKey(
        GamificationContext,
        related_name="actions",
        on_delete=models.CASCADE,
    )
    action = models.CharField(choices=ACTIONS, max_length=100)
    parameters = models.JSONField(default=dict)

    points_awarded = models.PositiveIntegerField()
    badges_awarded = models.ManyToManyField(
        "BadgeDefinition",
        related_name="awarded_in_actions",
        blank=True,
    )


class Action(TimestampableModel):
    """
    A concrete instance of an action definition by a user
    """

    definition = models.ForeignKey(
        ActionDefinition,
        related_name="actions",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name="actions",
        on_delete=models.CASCADE,
    )


class BadgeDefinition(models.Model):
    """
    Defines a badge that can be earned by users in a specific context
    """

    name = models.TextField()  # TODO language awareness
    # TODO appearance params?
    context = models.ForeignKey(
        GamificationContext,
        related_name="badges",
        on_delete=models.CASCADE,
    )


class Badge(TimestampableModel):
    """
    Represents a concrete instance of a badge definition awarded to a user
    """

    badge_definition = models.ForeignKey(
        BadgeDefinition,
        related_name="badges",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name="badges",
        on_delete=models.CASCADE,
    )
