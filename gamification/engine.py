"""
Entry point to the app from the other apps
"""

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from notifications.signals import notify

from typing import Any, Dict, List, Optional, TypedDict
from gamification.actions import SUBMIT_EXERCISE_SOLUTION, VALID_ACTIONS
from gamification.models import (
    Action,
    ActionDefinition,
    GamificationContext,
    GamificationReputationDelta,
    Goal,
    GoalLevel,
    GoalProgress,
)
from gamification.notifications import NEW_GOAL_LEVEL_REACHED, NOTIFICATION_VERBS
from users.models import User


"""
When an action is dispatched, this is the algorithm:
- infer the context: for now, we'll just get the course and get its default context
(OR, get all contexts for involved objects)
- retrieve an ActionDefinition from the context and action code
- if no such ActionDefinition exists, STOP
- create an Action that points to the user and the ActionDefinition retrieved at point above
- award points and badges
- for all goals in the context, retrieve the current level for the user
- for all retrieved levels, check if user has requirements to complete level: if not, CONTINUE,
otherwise, award points & badges & notify
"""

# {
#     "action": VALID_ACTIONS[SUBMIT_EXERCISE_SOLUTION],
#     "object": ExerciseSolution.objects...,
#     "user": User.objects...,
#     "related_objects": [solution.exercise, solution.exercise.course, ...]
# }


class ActionPayload(TypedDict):
    action: str  # TODO must be one of VALID_ACTION - enforce
    main_object: Any  # the main model instance involved in the action
    user: User  # actor
    related_objects: List[
        Any
    ]  # other related objects that could have GamificationContexts associated
    extras: Dict[str, Any]


def dispatch_action(payload: ActionPayload) -> None:
    contexts = get_contexts(payload["main_object"], *payload["related_objects"])
    user = payload["user"]

    # get gamification context(s) for all involved objects
    for context in contexts:
        # check if the action in payload is registered in current context
        action_definition = get_action_definition(payload["action"], context)
        if action_definition is None:
            continue
        # record action done by user
        action = record_action(action_definition, user)
        # if action has points or badges associated to it, award them
        action.award_reputation_and_badges(user)
        # if user has reached new levels or goals with this action, award them
        award_points_and_badges_for_progress(context, user)


def get_contexts(*args: Any) -> List[GamificationContext]:
    # TODO optimize
    ret: List[GamificationContext] = []
    for obj in args:
        object_content_type = ContentType.objects.get_for_model(obj)
        object_contexts = GamificationContext.objects.filter(
            content_type=object_content_type, object_id=obj.pk
        ).with_prefetched_related_objects()
        ret.extend([c for c in object_contexts])
    return ret


def get_action_definition(
    action_code: str, context: GamificationContext
) -> Optional[ActionDefinition]:
    try:
        return context.action_definitions.get(action_code=action_code)  # type: ignore
    except ActionDefinition.DoesNotExist:
        return None


def record_action(action_definition: ActionDefinition, user: User) -> Action:
    return Action.objects.create(user=user, definition=action_definition)


# def award_points_and_badges_for_action(action: Action, user: User) -> None:
#     GamificationReputationDelta.objects.create(
#         user=user,
#         context=action.definition.context,
#         delta=action.definition.reputation_awarded,
#     )


def award_points_and_badges_for_progress(
    context: GamificationContext, user: User
) -> None:
    for goal in context.goals.all():
        goal_progress: GoalProgress = goal.progresses.get_or_create(user=user)[0]
        highest_level_satisfied: GoalLevel = (
            goal.levels.all()
            .prefetch_related("requirements")
            .get_highest_satisfied_by_user(
                user, starting_from=goal_progress.current_level
            )
        )
        if highest_level_satisfied == goal_progress.current_level:
            # user hasn't reached a new level
            continue

        # for all new levels the user has reached for this goal,
        # award badges and reputation
        for reached_level in goal.levels.filter(
            level_value__gt=goal_progress.current_level.level_value
            if goal_progress.current_level is not None
            else 0,
            level_value__lte=highest_level_satisfied.level_value
            if highest_level_satisfied is not None
            else 0,
        ):
            # notify user about new reached level
            notify.send(
                user,
                recipient=user,
                action_object=reached_level,
                target=goal,
                verb=NOTIFICATION_VERBS[NEW_GOAL_LEVEL_REACHED],
            )
            reached_level.award_reputation_and_badges(user)

        # update goal progress to reflect new highest reached level
        goal_progress.reach_level(highest_level_satisfied)
