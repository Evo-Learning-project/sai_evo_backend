from rest_framework import serializers
from .models import (
    GamificationContext,
    Goal,
    GoalLevel,
    GoalLevelActionDefinitionRequirement,
)
from users.models import User


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
        models = GoalLevel
        fields = ["id", "level_value", "requirements"]


class GoalSerializer(serializers.ModelSerializer):
    levels = GoalLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Goal
        fields = ["id", "name", "levels"]


class GamificationContextSerializer(serializers.ModelSerializer):
    reputation = serializers.SerializerMethodField()

    class Meta:
        model = GamificationContext
        fields = ["id", "reputation", "badges", "goals"]

    def get_reputation(self, obj):
        return obj.get_reputation_for(self.context["request"].user)


class GamificationUserSerializer(serializers.ModelSerializer):
    reputation = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "reputation", "badges"]

    def get_badges(self, obj):
        return []

    def get_reputation(self, obj):
        return self.context["gamification_context"].get_reputation_for(obj)
