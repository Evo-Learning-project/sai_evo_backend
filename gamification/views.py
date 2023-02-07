from rest_framework import viewsets
from django.db.models import Prefetch

from gamification.models import (
    GamificationContext,
    Goal,
    GamificationReputationDelta,
    GoalLevel,
)
from gamification.pagination import LeaderboardPagination
from gamification import policies

from gamification.serializers import (
    GamificationContextSerializer,
    GamificationUserSerializer,
    GoalLevelSerializer,
    GoalProgressSerializer,
    GoalSerializer,
)
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404


class GoalLevelViewSet(viewsets.ModelViewSet):
    serializer_class = GoalLevelSerializer
    queryset = GoalLevel.objects.all()
    permission_classes = [policies.GamificationGoalAccessPolicy]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                context_id=self.kwargs["context_pk"],
                goal_id=self.kwargs["goal_pk"],
            )
        )

    def perform_create(self, serializer):
        serializer.save(
            goal_id=self.kwargs.get("goal_pk"),
            # user=self.request.user,
        )


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    queryset = Goal.objects.all()
    permission_classes = [policies.GamificationGoalAccessPolicy]

    def get_queryset(self):
        return super().get_queryset().filter(context_id=self.kwargs["context_pk"])

    def perform_create(self, serializer):
        serializer.save(
            context_id=self.kwargs.get("context_pk"),
            # user=self.request.user,
        )

    @action(methods=["get"], detail=True)
    def progress(self, request, **kwargs):
        goal: Goal = self.get_object()

        goal_progress = get_object_or_404(goal.progresses.all(), user=request.user)
        return Response(GoalProgressSerializer(goal_progress).data)


class CourseGamificationContextViewSet(viewsets.GenericViewSet):
    serializer_class = GamificationContextSerializer
    queryset = GamificationContext.objects.all()
    permission_classes = [policies.GamificationContextAccessPolicy]

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
        ordered_active_users = gamification_context.get_leaderboard().prefetch_related(
            Prefetch(
                "reputation_deltas",
                queryset=GamificationReputationDelta.objects.filter(
                    context=gamification_context
                ),
                to_attr="prefetched_reputation_deltas",
            ),
        )

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
