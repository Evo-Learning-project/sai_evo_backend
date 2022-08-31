from gamification.models import Goal, GoalLevel
from gamification.serializers import GoalLevelSerializer, GoalSerializer

NEW_GOAL_LEVEL_REACHED = "gamification.NEW_GOAL_LEVEL_REACHED"

NOTIFICATION_VERBS = {
    NEW_GOAL_LEVEL_REACHED: NEW_GOAL_LEVEL_REACHED,
}


NOTIFICATION_SERIALIZER_GENERIC_RELATION_MAPPING = {
    GoalLevel: GoalLevelSerializer,
    Goal: GoalSerializer,
}
