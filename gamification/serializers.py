from rest_framework import serializers
from .models import GamificationContext


class GamificationContextSerializer(serializers.ModelSerializer):
    reputation = serializers.SerializerMethodField()

    class Meta:
        model = GamificationContext
        fields = ["id", "reputation", "badges", "goals"]

    def get_reputation(self, obj):
        return obj.get_reputation_for(self.context["request"].user)
