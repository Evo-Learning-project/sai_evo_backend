from django.db import models
from django.db.models.aggregates import Max, Min, Count

from users.models import User


class GamificationContextQuerySet(models.QuerySet):
    def with_prefetched_related_objects(self):
        return self.prefetch_related(
            "goals",
            "goals__levels",
            "action_definitions",
            "badges",
            "badges__badges",
            "goals__levels__requirements",
            "goals__progresses",
            "reputation_deltas",
        )


class GoalLevelQuerySet(models.QuerySet):
    def get_highest_satisfied_by_user(self, user: User, starting_from):
        if self.first() is None:
            return None

        self = self.order_by("level_value").filter(
            level_value__gte=starting_from.level_value
            if starting_from is not None
            else 0
        )

        context = self.first().goal.context
        user_actions_with_amounts = (
            user.actions.filter(  # type: ignore
                definition__context=context,
            )
            .values("definition")
            .annotate(action_count=Count("definition"))
        )
        """
        <QuerySet [
            {'definition': 2, 'definition_count': 2},
            {'definition': 3, 'definition_count': 1}
        ]>
        """
        # print(user_actions_with_amounts)

        highest_reached_level = None

        # for each level, check if the requirements are met by user
        for level in self:
            reached = True
            # iterate over the level's requirements and see if they are satisfied
            for requirement in level.requirements.all():
                action_count = next(
                    (
                        pair
                        for pair in user_actions_with_amounts
                        if pair["definition"] == requirement.action_definition.pk
                    ),
                    {"action_count": 0},
                )["action_count"]
                # requirement not satisfied; level not reached
                if action_count < requirement.amount:
                    reached = False
                    break
            if reached:
                highest_reached_level = level

        return highest_reached_level
