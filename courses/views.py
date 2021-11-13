from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventTemplate,
    Exercise,
    ParticipationSubmissionSlot,
)

from .serializers import (
    CourseSerializer,
    EventParticipationSerializer,
    EventParticipationSlotSerializer,
    EventSerializer,
    EventTemplateSerializer,
    ExerciseSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    # TODO filter access so students can see all
    # courses and teachers only the ones they teach

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
        )


class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer
    queryset = Exercise.objects.all().prefetch_related(
        "tags",
        "choices",
        "testcases",
        "sub_exercises",
    )
    # TODO permissions - only teachers should access this viewset directly
    # TODO filtering - by course, tag, type, slug (?)


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    # TODO filter by course, type, begin_timestamp, state
    # TODO read-only for students


class EventTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = EventTemplateSerializer
    queryset = EventTemplate.objects.public()  # TODO make this

    # TODO filter by course


class EventParticipationViewSet(viewsets.ModelViewSet):
    serializer_class = EventParticipationSerializer
    queryset = EventParticipation.objects.all().select_related(
        "assessment",
        "submission",
    )

    # TODO filter by course, state, assessment state?


class EventParticipationSlotViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = EventParticipationSlotSerializer
    queryset = ParticipationSubmissionSlot.objects.all().prefetch_related("sub_slots")
    lookup_field = "slot_number"

    def get_queryset(self):
        qs = super().get_queryset().base_slots()  # TODO change this
        # print(self.kwargs["participation_pk"])
        return qs.filter(submission__participation=self.kwargs["participation_pk"])
