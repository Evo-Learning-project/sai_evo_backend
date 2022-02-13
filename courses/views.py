from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User
from users.serializers import UserSerializer

from courses import policies
from courses.logic import privileges
from courses.logic.privileges import check_privilege
from courses.models import (
    Course,
    CourseRole,
    Event,
    EventParticipation,
    EventTemplate,
    EventTemplateRule,
    EventTemplateRuleClause,
    Exercise,
    ExerciseChoice,
    ParticipationAssessmentSlot,
    ParticipationSubmissionSlot,
    Tag,
    UserCoursePrivilege,
)
from courses.pagination import ExercisePagination

from .serializers import (
    CourseRoleSerializer,
    CourseSerializer,
    EventSerializer,
    EventTemplateRuleClauseSerializer,
    EventTemplateRuleSerializer,
    EventTemplateSerializer,
    ExerciseChoiceSerializer,
    ExerciseSerializer,
    ParticipationAssessmentSlotSerializer,
    ParticipationSubmissionSlotSerializer,
    StudentViewEventParticipationSerializer,
    TagSerializer,
    TeacherViewEventParticipationSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    permission_classes = [policies.CoursePolicy]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "list":
            context["preview"] = True
        return context

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
        )

    # @action(detail=True, methods=["get"])
    # def enrolled(self, request, **kwargs):
    #     course = self.get_object()
    #     serializer = UserSerializer(course.enrolled_users.all(), many=True)
    #     return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def set_permissions(self, request, **kwargs):
        course = self.get_object()
        try:
            user = get_object_or_404(User, pk=request.data["user"])
        except KeyError:
            return Response(status=status.HTTP_404_BAD_REQUEST)

        _, created = UserCoursePrivilege.create_or_update(
            user=user,
            course=course,
            defaults={
                "allow_privileges": request.data.get("allow_privileges", []),
                "deny_privileges": request.data.get("deny_privileges", []),
            },
        )

        return Response(
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class CourseRoleViewSet(viewsets.ModelViewSet):
    serializer_class = CourseRoleSerializer
    queryset = CourseRole.objects.all()
    permission_classes = [policies.CourseRolePolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(course_id=self.kwargs["course_pk"])

    @action(detail=True, methods=["get"])
    def add_to_user(self, request, **kwargs):
        role = self.get_object()
        try:
            user = get_object_or_404(User, pk=request.data["user"])
        except KeyError:
            return Response(status=status.HTTP_404_BAD_REQUEST)

        user.roles.add(role)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def remove_from_user(self, request, **kwargs):
        role = self.get_object()
        try:
            user = get_object_or_404(User, pk=request.data["user"])
        except KeyError:
            return Response(status=status.HTTP_404_BAD_REQUEST)

        user.roles.remove(role)
        return Response(status=status.HTTP_200_OK)


class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer
    queryset = Exercise.objects.all().prefetch_related(
        "tags",
        "choices",
        "testcases",
        "sub_exercises",
    )
    permission_classes = [policies.ExercisePolicy]
    pagination_class = ExercisePagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["label", "text"]

    def get_permissions(self):
        if self.kwargs.get("exercise_pk"):
            # accessing a sub-exercise
            self.permission_classes = [policies.ExerciseRelatedObjectsPolicy]

        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # this viewset is meant to be accessed by privileged users, therefore
        # they need to be able to access the hidden serializer fields
        context["show_hidden_fields"] = True
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(course_id=self.kwargs["course_pk"])
        if self.kwargs.get("exercise_pk") is not None:
            # using the viewset for sub-exercises
            qs = qs.filter(parent_id=self.kwargs["exercise_pk"])
        else:
            qs = qs.base_exercises()

        return qs

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            parent_id=self.kwargs.get("exercise_pk"),
        )

    @action(detail=False, methods=["get"])
    def bulk_get(self, request, **kwargs):
        try:
            ids = request.query_params["ids"]
            id_list = ids.split(",")
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        exercises = []
        course = get_object_or_404(Course, pk=self.kwargs["course_pk"])

        for pk in id_list:
            exercise = get_object_or_404(self.get_queryset(), pk=pk)
            exercises.append(exercise)

        serializer = self.get_serializer_class()(
            data=exercises,
            many=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=True, methods=["put", "delete"])
    def tags(self, request, **kwargs):
        exercise = self.get_object()
        try:
            text = request.data["tag"]
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.method == "PUT":
            # create tag if it doesn't exist already
            tag, _ = Tag.objects.get_or_create(course_id=kwargs["course_pk"], name=text)

            exercise.tags.add(tag)
        elif request.method == "DELETE":
            # remove tag from exercise
            tag = get_object_or_404(
                Tag.objects.filter(course_id=kwargs["course_pk"]), name=text
            )

            exercise.tags.remove(tag)
        else:
            assert False

        return Response(status=status.HTTP_204_NO_CONTENT)


class ExerciseChoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseChoiceSerializer
    queryset = ExerciseChoice.objects.all()
    permission_classes = [policies.ExerciseRelatedObjectsPolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(exercise_id=self.kwargs["exercise_pk"])

    def perform_create(self, serializer):
        serializer.save(
            exercise_id=self.kwargs["exercise_pk"],
        )


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    # mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [policies.TagPolicy]

    # TODO abstract this behavior
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(course_id=self.kwargs["course_pk"])

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            creator=self.request.user,
        )


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.all()
    permission_classes = [policies.EventPolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(course_id=self.kwargs["course_pk"])

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            creator=self.request.user,
        )


class EventTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = EventTemplateSerializer
    queryset = EventTemplate.objects.public()
    permission_classes = [policies.EventTemplatePolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(course_id=self.kwargs["course_pk"])

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            creator=self.request.user,
        )


class EventTemplateRuleViewSet(viewsets.ModelViewSet):
    serializer_class = EventTemplateRuleSerializer
    queryset = EventTemplateRule.objects.all()
    permission_classes = [policies.EventTemplatePolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            template_id=self.kwargs["template_pk"],
        )

    def perform_create(self, serializer):
        serializer.save(template_id=self.kwargs["template_pk"])


class EventTemplateRuleClauseViewSet(viewsets.ModelViewSet):
    serializer_class = EventTemplateRuleClauseSerializer
    queryset = EventTemplateRuleClause.objects.all()
    permission_classes = [policies.EventTemplatePolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            rule_id=self.kwargs["rule_pk"],
        )

    def perform_create(self, serializer):
        serializer.save(rule_id=self.kwargs["rule_pk"])


class EventParticipationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):

    """
    Viewset for creating, accessing, and updating participations to events

    Non-privileged users (i.e. students) can POST to this viewset to create a
    participation to an event (i.e. to participate in the event), and update
    the status of their participation (e.g. turn in)

    Privileged users such as teachers can access all the participations to
    relevant events and update the statuses relative to the assessments
    """

    queryset = EventParticipation.objects.all().select_related(
        "assessment",
        "submission",
    )
    permission_classes = [policies.EventParticipationPolicy]

    def get_serializer_class(self):
        return (
            TeacherViewEventParticipationSerializer
            if check_privilege(
                self.request.user,
                self.kwargs["course_pk"],
                privileges.ASSESS_PARTICIPATIONS,
            )
            else StudentViewEventParticipationSerializer
        )

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            event_instance__isnull=False,
            event_instance__event_id=self.kwargs["event_pk"],
        )

    def create(self, request, *args, **kwargs):

        # cannot use get_or_create because the custom manager won't be called
        # participation, _ = self.get_queryset().get_or_create(user=request.user)
        try:
            participation = self.get_queryset().get(user=request.user)
        except EventParticipation.DoesNotExist:
            participation = EventParticipation.objects.create(
                user=request.user, event_id=self.kwargs["event_pk"]
            )

        serializer = StudentViewEventParticipationSerializer(participation)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"])
    def bulk_patch(self, request, **kwargs):
        try:
            ids = request.query_params["ids"]
            id_list = ids.split(",")
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        print(request.data)
        ret = []
        for pk in id_list:
            participation = get_object_or_404(self.get_queryset(), pk=pk)
            ret.append(participation)

            serializer = TeacherViewEventParticipationSerializer(
                participation, data=data, partial=True
            )
            serializer.is_valid()
            serializer.save()

        serializer = TeacherViewEventParticipationSerializer(ret, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def go_forward(self, request, **kwargs):
        participation = self.get_object()
        participation.move_current_slot_cursor_forward()

        current_slot = participation.submission.current_slots[0]
        serializer = ParticipationSubmissionSlotSerializer(current_slot)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def go_back(self, request, **kwargs):
        participation = self.get_object()
        participation.move_current_slot_cursor_back()

        current_slot = participation.submission.current_slots[0]
        serializer = ParticipationSubmissionSlotSerializer(current_slot)
        return Response(serializer.data)


class EventParticipationSlotViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for accessing and updating the individual slots of a participation

    Non-privileged users (i.e. students) can use PATCH requests to update the
    submissions to the assigned exercises (e.g. change the text of an open answer
    or the selected choice)

    Privileged users such as teachers can PATCH the slots to change the assigned
    score to a slot or to add comments to the assessment slot
    """

    permission_classes = [policies.EventParticipationSlotPolicy]

    def get_serializer_class(self):
        return (
            ParticipationAssessmentSlotSerializer
            if check_privilege(
                self.request.user,
                self.kwargs["course_pk"],
                privileges.ASSESS_PARTICIPATIONS,
            )
            else ParticipationSubmissionSlotSerializer
        )

    def get_queryset(self):
        if check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.ASSESS_PARTICIPATIONS,
        ):
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
