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
    ParticipationAssessmentSlot,
    ParticipationSubmissionSlot,
)

from .serializers import CourseSerializer  # EventParticipationSerializer,
from .serializers import (
    EventSerializer,
    EventTemplateSerializer,
    ExerciseSerializer,
    ParticipationAssessmentSlotSerializer,
    ParticipationSubmissionSlotSerializer,
    StudentViewEventParticipationSerializer,
    TeacherViewEventParticipationSerializer,
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


class EventParticipationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    # serializer_class = TeacherViewEventParticipationSerializer
    queryset = EventParticipation.objects.all().select_related(
        "assessment",
        "submission",
    )

    def get_serializer_class(self):
        return (
            TeacherViewEventParticipationSerializer
            if self.request.user.is_teacher
            else StudentViewEventParticipationSerializer
        )

    # TODO filter by course, state, assessment state?

    def create(self, request, *args, **kwargs):
        # TODO if participation already exists, return that one, otherwise create it
        return super().create(request, *args, **kwargs)


class EventParticipationSlotViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    # serializer_class = ParticipationAssessmentSlotSerializer
    # queryset = ParticipationAssessmentSlot.objects.all().prefetch_related("sub_slots")

    def get_serializer_class(self):
        return (
            ParticipationAssessmentSlotSerializer
            if self.request.user.is_teacher
            else ParticipationSubmissionSlotSerializer
        )

    def get_queryset(self):
        if self.request.user.is_teacher:
            qs = ParticipationAssessmentSlot.objects.all()
            related_kwarg = {
                "assessment__participation": self.kwargs["participation_pk"]
            }
        else:
            qs = ParticipationSubmissionSlot.objects.all()
            related_kwarg = {
                "submission__participation": self.kwargs["participation_pk"]
            }

        return qs.filter(**related_kwarg).prefetch_related("sub_slots")
