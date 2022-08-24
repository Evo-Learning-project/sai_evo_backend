"""
Entry point to the app from the other apps
"""


from typing import Any, Dict, List, Optional, TypedDict
from gamification.actions import SUBMIT_EXERCISE_SOLUTION, VALID_ACTIONS
from gamification.models import Action, ActionDefinition, GamificationContext
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
- for all retrieved levels, check if user has requirements to complete level: if not, CONTINUE, otherwise, award points & badges & notify
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

    # get gamification context(s) for all involved objects
    for context in contexts:
        # check if the action in payload is registered in current context
        action_definition = get_action_definition(payload["action"], context)
        if action_definition is None:
            continue
        # record action done by user
        action = record_action(action_definition, payload["user"])
        # if action has points or badges associated to it, award them
        award_points_and_badges_for_action(action)
        # if user has reached new levels or goals with this action, award them
        award_points_and_badges_for_progress(payload["user"], context)


def get_contexts(*args: List[Any]) -> List[GamificationContext]:
    ...


def get_action_definition(
    action_code: str, context: GamificationContext
) -> Optional[ActionDefinition]:
    ...


def record_action(action_definition: ActionDefinition, user: User) -> Action:
    return Action.objects.create(user=user, definition=action_definition)


def award_points_and_badges_for_action(action: Action) -> None:
    ...


def award_points_and_badges_for_progress(
    user: User, context: GamificationContext
) -> None:
    ...
