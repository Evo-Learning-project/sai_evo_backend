from rest_framework import serializers
from .models import (
    GamificationContext,
    Goal,
    GoalLevel,
    GoalLevelActionDefinitionRequirement,
    GoalProgress,
)
from users.models import User

from django.db.models.aggregates import Max, Min, Count
from django.db.models import F


class GoalProgressSerializer(serializers.ModelSerializer):
    action_counts = serializers.SerializerMethodField()
    current_level = serializers.IntegerField(
        read_only=True, source="current_level.level_value"
    )

    class Meta:
        model = GoalProgress
        fields = ["current_level", "action_counts"]

    def get_action_counts(self, obj: GoalProgress):
        # TODO review
        user = obj.user
        return (
            user.actions.filter(
                definition__context=obj.goal.context,
            )
            .annotate(action=F("definition__action_code"))
            .values("action")
            .annotate(amount=Count("definition"))
        )


class GoalLevelActionDefinitionRequirementSerializer(serializers.ModelSerializer):
    action = serializers.CharField(source="action_definition.action_code")

    class Meta:
        model = GoalLevelActionDefinitionRequirement
        fields = ["action", "amount"]


class GoalLevelSerializer(serializers.ModelSerializer):
    requirements = GoalLevelActionDefinitionRequirementSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = GoalLevel
        fields = ["id", "level_value", "requirements"]


class GoalSerializer(serializers.ModelSerializer):
    levels = GoalLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Goal
        fields = ["id", "name", "levels"]


class GamificationContextSerializer(serializers.ModelSerializer):
    reputation = serializers.SerializerMethodField()
    leaderboard_position = serializers.SerializerMethodField()

    class Meta:
        model = GamificationContext
        fields = ["id", "reputation", "badges", "goals", "leaderboard_position"]

    def get_reputation(self, obj: GamificationContext):
        return obj.get_reputation_for(self.context["request"].user)

    def get_leaderboard_position(self, obj: GamificationContext):
        return obj.get_leaderboard_position_for(self.context["request"].user)


class GamificationUserSerializer(serializers.ModelSerializer):
    reputation = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "reputation", "badges", "avatar_url"]

    def get_badges(self, obj):
        return []

    def get_reputation(self, obj):
        return self.context["gamification_context"].get_reputation_for(obj)
