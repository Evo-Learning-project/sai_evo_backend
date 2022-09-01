from django.db import models
from gamification.actions import VALID_ACTIONS
from gamification.managers import GoalLevelManager
from users.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Case, When, Value

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

    # TODO enforce uniqueness per content_object

    def __str__(self) -> str:
        return "Context " + str(self.pk) + " - " + str(self.content_object)[:50]

    def get_reputation_for(self, user: User):
        return user.reputation_deltas.filter(context=self).aggregate(
            reputation_total=Sum("delta", default=0),
        )["reputation_total"]

    def get_users_with_annotated_reputation_total(self):
        # TODO filter for deltas in this context
        return User.objects.all().annotate(
            reputation_total=Sum("reputation_deltas__delta", default=0)
        )

    def get_active_users(self):
        return self.get_users_with_annotated_reputation_total().filter(
            reputation_total__gt=0
        )

    def get_leaderboard(self):
        return self.get_active_users().order_by("-reputation_total")

    def get_leaderboard_position_for(self, user: User):
        qs = self.get_leaderboard()
        # TODO optimize
        # numbered_qs = qs.extra(
        #     select={
        #         "queryset_row_number": 'ROW_NUMBER() OVER (ORDER BY "users_user"."id")'
        #     }
        # )
        # print("NUM", numbered_qs)
        try:
            return list(qs.values_list("id", flat=True)).index(user.pk) + 1
        except ValueError:
            return None


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

    def __str__(self) -> str:
        return "Goal " + self.name


class GoalLevel(models.Model):
    goal = models.ForeignKey(
        Goal,
        related_name="levels",
        on_delete=models.CASCADE,
    )

    action_requirements = models.ManyToManyField(
        "ActionDefinition",
        through="GoalLevelActionDefinitionRequirement",
    )

    level_value = models.PositiveIntegerField()
    reputation_awarded = models.PositiveIntegerField()
    badges_awarded = models.ManyToManyField(
        "BadgeDefinition",
        related_name="awarded_in_goal_levels",
        blank=True,
    )

    objects = GoalLevelManager()

    def __str__(self) -> str:
        return str(self.goal) + " level " + str(self.level_value)

    def award_reputation_and_badges(self, to_user: User):
        # TODO deal with badges
        GamificationReputationDelta.objects.create(
            user=to_user,
            context=self.goal.context,
            delta=self.reputation_awarded,
        )


class ActionDefinition(models.Model):
    """
    An action that can be done by a user in a specific context
    """

    ACTIONS = [(k, v) for k, v in VALID_ACTIONS.items()]

    context = models.ForeignKey(
        GamificationContext,
        related_name="action_definitions",
        on_delete=models.CASCADE,
    )
    action_code = models.CharField(choices=ACTIONS, max_length=100)
    # TODO allow parametrizing actions
    # parameters = models.JSONField(default=dict, blank=True)

    reputation_awarded = models.PositiveIntegerField()
    badges_awarded = models.ManyToManyField(
        "BadgeDefinition",
        related_name="awarded_in_actions",
        blank=True,
    )

    def __str__(self) -> str:
        return "Action " + self.action_code + " in context " + str(self.context)


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
    # parameters = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return str(self.pk) + " " + str(self.definition) + " by " + str(self.user)

    def award_reputation_and_badges(self, to_user: User):
        GamificationReputationDelta.objects.create(
            user=to_user,
            context=self.definition.context,
            delta=self.definition.reputation_awarded,
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

    def __str__(self) -> str:
        return "Badge " + self.name + " in context " + str(self.pk)


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

    def __str__(self) -> str:
        return str(self.badge_definition) + " of " + str(self.user)


class GoalLevelActionDefinitionRequirement(models.Model):
    """
    A requirement to finish a goal level, i.e. an action and the amount of
    times it must be performed to satisfy the requirement
    """

    goal_level = models.ForeignKey(
        GoalLevel,
        related_name="requirements",
        on_delete=models.CASCADE,
    )
    action_definition = models.ForeignKey(ActionDefinition, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    def __str__(self) -> str:
        return (
            "("
            + str(self.goal_level)
            + ") "
            + str(self.action_definition)
            + ": "
            + str(self.amount)
        )


class GoalProgress(models.Model):
    """
    The progress a user has made towards clearing a goal, i.e. their
    current level of achievement for that goal
    """

    goal = models.ForeignKey(
        Goal,
        related_name="progresses",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name="goal_progresses",
        on_delete=models.CASCADE,
    )
    current_level = models.ForeignKey(
        GoalLevel,
        related_name="current_in_progresses",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return (
            str(self.user)
            + " - "
            + str(self.goal)
            + ": "
            + str(self.current_level.level_value)
        )

    # TODO enforce that current_level is child of goal

    def reach_level(self, new_level: GoalLevel):
        self.current_level = new_level
        self.save(update_fields=["current_level"])


class GamificationReputationDelta(TimestampableModel):
    """
    Represents an increase or decrease in the reputation score of a user
    in a particular gamification context.
    """

    context = models.ForeignKey(
        GamificationContext,
        related_name="reputation_deltas",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name="reputation_deltas",
        on_delete=models.CASCADE,
    )
    delta = models.IntegerField()
    data = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return str(self.user) + ": " + str(self.delta) + " (" + str(self.context) + ")"
