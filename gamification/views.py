from rest_framework import filters, mixins, status, viewsets
from courses.models import Course

from gamification.models import GamificationContext, Goal
from django.contrib.contenttypes.models import ContentType
from gamification.pagination import LeaderboardPagination

from gamification.serializers import (
    GamificationContextSerializer,
    GamificationUserSerializer,
    GoalProgressSerializer,
    GoalSerializer,
)
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    queryset = Goal.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(context_id=self.kwargs["context_pk"])

    @action(methods=["get"], detail=True)
    def progress(self, request, **kwargs):
        goal: Goal = self.get_object()

        goal_progress = get_object_or_404(goal.progresses.all(), user=request.user)
        return Response(GoalProgressSerializer(goal_progress).data)


class CourseGamificationContextViewSet(viewsets.ModelViewSet):
    serializer_class = GamificationContextSerializer
    queryset = GamificationContext.objects.all()
    permission_classes = []

    # TODO implement method to create gamification context for a course

    @property
    def paginator(self):
        """
        Paginate only action `leaderboard`
        """
        if self.action == "leaderboard" and not hasattr(self, "_paginator"):
            self._paginator = LeaderboardPagination()
        return super().paginator

    @action(methods=["get"], detail=True)
    def leaderboard(self, request, **kwargs):
        gamification_context = self.get_object()
        ordered_active_users = gamification_context.get_leaderboard()

        page = self.paginate_queryset(ordered_active_users)

        if page is not None:
            serializer = GamificationUserSerializer(
                page,
                many=True,
                context={"gamification_context": gamification_context},
            )
            return self.get_paginated_response(serializer.data)

        serializer = GamificationUserSerializer(
            ordered_active_users,
            many=True,
            context={"gamification_context": gamification_context},
        )
        return Response(serializer.data)
