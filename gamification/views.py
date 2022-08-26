from rest_framework import filters, mixins, status, viewsets
from courses.models import Course

from gamification.models import GamificationContext
from django.contrib.contenttypes.models import ContentType

from gamification.serializers import (
    GamificationContextSerializer,
    GamificationUserSerializer,
)
from rest_framework.response import Response
from rest_framework.decorators import action


class CourseGamificationContextViewSet(viewsets.ModelViewSet):
    serializer_class = GamificationContextSerializer
    queryset = GamificationContext.objects.all()
    permission_classes = []

    # TODO implement method to create gamification context for a course

    @action(methods=["get"], detail=True)
    def leaderboard(self, request, **kwargs):
        gamification_context = self.get_object()
        ordered_active_users = gamification_context.get_active_users().order_by(
            "-reputation_total"
        )
        serializer = GamificationUserSerializer(
            ordered_active_users,
            many=True,
            context={"gamification_context": gamification_context},
        )

        return Response(serializer.data)
