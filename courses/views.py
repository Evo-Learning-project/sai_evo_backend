import json
import os
import time
from django.db.models import Q


from django.db.models import Exists, OuterRef
from django.db.models import Prefetch
from drf_viewset_profiler import line_profiler_viewset


import django_filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from coding.helpers import get_code_execution_results
from courses.logic.event_instances import get_exercises_from
from courses.logic.presentation import (
    CHOICE_SHOW_SCORE_FIELDS,
    EVENT_PARTICIPATION_SHOW_SLOTS,
    EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS,
    EVENT_SHOW_HIDDEN_FIELDS,
    EVENT_SHOW_PARTICIPATION_EXISTS,
    EVENT_SHOW_TEMPLATE,
    EVENT_TEMPLATE_RULE_SHOW_SATISFYING_FIELD,
    EXERCISE_SHOW_HIDDEN_FIELDS,
    EXERCISE_SHOW_SOLUTION_FIELDS,
    TAG_SHOW_PUBLIC_EXERCISES_COUNT,
    TESTCASE_SHOW_HIDDEN_FIELDS,
)
from courses.tasks import run_user_code_task
from users.models import User
from users.serializers import UserSerializer
from django.http import FileResponse, Http404
from courses import policies
from courses.logic import privileges
from courses.logic.privileges import check_privilege
from courses.models import (
    Course,
    CourseRole,
    Event,
    EventParticipation,
    EventParticipationSlot,
    EventTemplate,
    EventTemplateRule,
    EventTemplateRuleClause,
    Exercise,
    ExerciseChoice,
    ExerciseTestCase,
    Tag,
    UserCoursePrivilege,
)
from courses.pagination import ExercisePagination

from .serializers import (
    CourseRoleSerializer,
    CourseSerializer,
    EventParticipationSerializer,
    EventParticipationSlotSerializer,
    EventSerializer,
    EventTemplateRuleClauseSerializer,
    EventTemplateRuleSerializer,
    EventTemplateSerializer,
    ExerciseChoiceSerializer,
    ExerciseSerializer,
    ExerciseTestCaseSerializer,
    TagSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = (
        Course.objects.all()
        .select_related("creator")
        .prefetch_related(
            "exercises",
            "exercises__public_tags",
            "exercises__private_tags",
            "exercises__choices",
            "exercises__testcases",
            "exercises__sub_exercises",
            "events",
            "events__template",
            "events__template__rules",
            "events__template__rules__clauses",
            "events__template__rules__clauses__tags",
            "events__template__rules__exercises",
            "roles",
            "roles__users",
            "privileged_users",
            "privileged_users__user",
        )
    )
    permission_classes = [policies.CoursePolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_teacher:
            qs = qs.public()

        qs = qs.prefetch_related(
            Prefetch(
                "privileged_users",
                queryset=UserCoursePrivilege.objects.filter(user=self.request.user),
                to_attr="prefetched_privileged_users",
            ),
            Prefetch(
                "roles",
                queryset=self.request.user.roles.all(),
                to_attr="prefetched_user_roles",
            ),
        )

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "list":
            context["preview"] = True
        return context

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
        )

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

    @action(detail=True, methods=["get"])
    def active_users(self, request, **kwargs):
        active_users = User.objects.all().active_in_course(self.kwargs["pk"])
        serializer = UserSerializer(active_users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def unstarted_practice_events(self, request, **kwargs):
        # sub-query that retrieves a user's participation to events
        exists_user_participation = (
            EventParticipation.objects.all()
            .with_prefetched_base_slots()
            .filter(user=request.user, event=OuterRef("pk"))
        )

        practice_events = Event.objects.annotate(
            user_participation_exists=Exists(exists_user_participation)
        ).filter(
            creator=request.user,
            course=self.get_object(),
            event_type=Event.SELF_SERVICE_PRACTICE,
            user_participation_exists=False,
        )

        return EventSerializer(practice_events, many=True, context=self.context).data


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


class ExerciseFilter(FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(), method="tags_filter"
    )

    class Meta:
        model = Exercise
        fields = ["tags", "exercise_type", "state"]

    def tags_filter(self, queryset, name, value):
        for tag in value:
            filter_cond = Q(public_tags__in=[tag]) | Q(private_tags__in=[tag])
            queryset = queryset.filter(filter_cond).distinct()
        return queryset


class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer
    queryset = Exercise.objects.all().prefetch_related(
        "private_tags",
        "public_tags",
        "choices",
        "testcases",
        "sub_exercises",
        "sub_exercises__choices",
        "sub_exercises__testcases",
        "sub_exercises__private_tags",
        "sub_exercises__public_tags",
        "sub_exercises__sub_exercises",
    )
    permission_classes = [policies.ExercisePolicy]
    pagination_class = ExercisePagination
    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
    ]
    filterset_class = ExerciseFilter
    search_fields = ["label", "text"]
    # filter_fields = ["exercise_type", "state"]

    def get_permissions(self):
        if self.kwargs.get("exercise_pk"):
            # accessing a sub-exercise
            self.permission_classes = [policies.ExerciseRelatedObjectsPolicy]

        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # this viewset is meant to be accessed by privileged users, therefore
        # they need to be able to access the hidden serializer fields
        context[EXERCISE_SHOW_SOLUTION_FIELDS] = True
        context[EXERCISE_SHOW_HIDDEN_FIELDS] = True
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(course_id=self.kwargs["course_pk"])
        if self.kwargs.get("exercise_pk") is not None:
            # using the viewset for sub-exercises
            qs = qs.filter(parent_id=self.kwargs["exercise_pk"])
        elif self.action == "list":
            qs = qs.base_exercises()

        return qs

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            parent_id=self.kwargs.get("exercise_pk"),
            creator=self.request.user,
        )

    # bulk creation
    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)

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
            public = request.data["public"]
            text = request.data["tag"]

            tags = exercise.public_tags if public else exercise.private_tags
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.method == "PUT":
            # create tag if it doesn't exist already
            tag, _ = Tag.objects.get_or_create(course_id=kwargs["course_pk"], name=text)

            tags.add(tag)
        elif request.method == "DELETE":
            # remove tag from exercise
            tag = get_object_or_404(
                Tag.objects.filter(course_id=kwargs["course_pk"]), name=text
            )

            tags.remove(tag)
        else:
            assert False

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def solution_execution_results(self, request, **kwargs):
        exercise = self.get_object()
        results = get_code_execution_results(
            exercise=exercise,
            code=exercise.solution,
        )
        return Response(results)


class ExerciseChoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseChoiceSerializer
    queryset = ExerciseChoice.objects.all()
    permission_classes = [policies.ExerciseRelatedObjectsPolicy]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # this viewset is meant to be accessed by privileged users, therefore
        # they need to be able to access the hidden serializer fields
        context[CHOICE_SHOW_SCORE_FIELDS] = True
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(exercise_id=self.kwargs["exercise_pk"])

    def perform_create(self, serializer):
        serializer.save(
            exercise_id=self.kwargs["exercise_pk"],
        )


class ExerciseTestCaseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseTestCaseSerializer
    queryset = ExerciseTestCase.objects.all()
    permission_classes = [policies.ExerciseRelatedObjectsPolicy]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # this viewset is meant to be accessed by privileged users, therefore
        # they need to be able to access the hidden serializer fields
        context[TESTCASE_SHOW_HIDDEN_FIELDS] = True
        return context

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
    viewsets.GenericViewSet,
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [policies.TagPolicy]

    # TODO abstract this behavior (filtering on course)
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(course_id=self.kwargs["course_pk"])

        qs = qs.with_prefetched_public_exercises().with_prefetched_public_unseen_exercises(
            self.request.user
        )

        # students can only access public tags
        if not check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.MANAGE_EXERCISES,
        ):
            qs = qs.public()

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "include_exercise_count" in self.request.query_params:
            context[TAG_SHOW_PUBLIC_EXERCISES_COUNT] = True
        return context

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            creator=self.request.user,
        )


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    queryset = (
        Event.objects.all()
        .select_related("template", "creator")
        .prefetch_related(
            "template__rules",
            "template__rules__exercises",
            "template__rules__clauses",
            "template__rules__clauses__tags",
            "users_allowed_past_closure",
        )
    )
    # TODO disallow list view for non-teachers (only allow students to retrieve an exam if they know the id)
    permission_classes = [policies.EventPolicy]
    filter_backends = [DjangoFilterBackend]
    filter_fields = ["event_type"]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(course_id=self.kwargs["course_pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context[EVENT_SHOW_HIDDEN_FIELDS] = check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.MANAGE_EVENTS,
        )
        context[EVENT_SHOW_PARTICIPATION_EXISTS] = self.action == "retrieve"
        context[EVENT_SHOW_TEMPLATE] = self.action != "list"
        return context

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            creator=self.request.user,
        )

    @action(methods=["get"], detail=True)
    def instances(self, request, **kwargs):
        instance_count = self.request.query_params.get("amount") or 5

        data = []
        template = self.get_object().template
        for _ in range(0, int(instance_count)):
            data.append(
                ExerciseSerializer(
                    get_exercises_from(template),
                    many=True,
                ).data
                # TODO? context to exercise serializer?
            )

        return Response(data)


# TODO disallow actions and make read-only
class EventTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = EventTemplateSerializer
    queryset = EventTemplate.objects.all()
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context[EVENT_TEMPLATE_RULE_SHOW_SATISFYING_FIELD] = check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.MANAGE_EXERCISES,
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            template_id=self.kwargs["template_pk"],
            search_public_tags_only=(
                # if rule was created by a student, rule should only search for public tags
                not check_privilege(
                    self.request.user,
                    self.kwargs["course_pk"],
                    privileges.MANAGE_EXERCISES,
                )
            ),
        )


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

    queryset = (
        EventParticipation.objects.all()
        .select_related(
            "user",
            "event",
        )
        .with_prefetched_base_slots()
    )
    permission_classes = [policies.EventParticipationPolicy]
    serializer_class = EventParticipationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context[EVENT_PARTICIPATION_SHOW_SLOTS] = True

        if self.action != "list":
            context[EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS] = True
        if self.action == "retrieve":
            # if a participation to a practice is being retrieved, show
            # solution fields
            participation = self.get_object()
            context[EXERCISE_SHOW_SOLUTION_FIELDS] = (
                participation.event.event_type == Event.SELF_SERVICE_PRACTICE
                or participation.is_assessment_available
            )
        elif self.request.query_params.get("preview") is not None:
            try:
                preview = json.loads(self.request.query_params["preview"])

                #! TODO FIXME context[EVENT_PARTICIPATION_SHOW_SLOTS] = not preview
                # ! have one parameter to define that you get the first n slots, and one to define
                # ! if you get all fields, for participation monitor you get all but no exercise field,
                # ! for student dashboard you get the first 3 with exercise and answer

                context[EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS] = True
                # downloading for csv
                # TODO use more explicit conditions (e.g. a "for_csv" query param)
                if not preview and self.action == "list":
                    context["trim_images_in_text"] = True
            except Exception:
                pass

        context["capabilities"] = self.get_capabilities()
        return context

    def get_capabilities(self):
        """
        Returns a dict for usage inside serializers' context in order to decide whether
        to display some fields ans whether to make them writable
        """
        force_student = "as_student" in self.request.query_params
        has_assess_privilege = check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.ASSESS_PARTICIPATIONS,
        )
        has_manage_events_privilege = check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.MANAGE_EVENTS,
        )

        ret = {
            # assessment fields are displayed to teachers at all times and to students
            # if the assessments have been published
            "assessment_fields_read": not force_student
            and (has_assess_privilege or has_manage_events_privilege)
            # accessing as student after the assessments are published
            or self.action == "retrieve" and self.get_object().is_assessment_available,
            # assessment fields are writable by teachers at all times
            "assessment_fields_write": has_assess_privilege,
            "submission_fields_read": True,
        }

        return ret

    def get_queryset(self):
        qs = super().get_queryset()
        try:
            if self.kwargs.get("event_pk") is not None:
                # accessing as a nested view of event viewset

                return qs.filter(
                    event_id=self.kwargs["event_pk"],
                )
            else:
                # accessing as a nested view of course viewset

                qs = qs.filter(event__course_id=self.kwargs["course_pk"])
                if self.request.query_params.get("user_id") is not None:
                    # only get participations of a specific user to a course
                    qs = qs.filter(user_id=self.request.query_params["user_id"])
                else:
                    # if user doesn't specify a user id, return their participations
                    qs = qs.filter(user=self.request.user)
                return qs
        except ValueError:
            raise Http404

    def create(self, request, *args, **kwargs):
        # cannot use get_or_create because the custom manager won't be called
        try:
            participation = self.get_queryset().get(user=request.user)
        except EventParticipation.DoesNotExist:
            try:
                participation_pk = EventParticipation.objects.create(
                    user=request.user, event_id=self.kwargs["event_pk"]
                ).pk
                participation = self.get_queryset().get(pk=participation_pk)
            except Event.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer_class()(
            participation, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=False, methods=["patch"])
    def bulk_patch(self, request, **kwargs):
        try:
            ids = request.query_params["ids"]
            id_list = ids.split(",")
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        ret = []
        for pk in id_list:
            participation = get_object_or_404(self.get_queryset(), pk=pk)
            ret.append(participation)

            serializer = self.get_serializer_class()(
                participation,
                context=self.get_serializer_context(),
                data=data,
                partial=True,
            )
            serializer.is_valid()
            serializer.save()

        serializer = self.get_serializer_class()(
            ret,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def go_forward(self, request, **kwargs):
        # TODO make this idempotent (e.g. include the target slot number in request)
        participation = self.get_queryset().get(pk=kwargs["pk"])
        participation.move_current_slot_cursor_forward()

        current_slot = participation.current_slots[0]
        serializer = EventParticipationSlotSerializer(
            current_slot,
            context={
                EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS: True,
                **self.get_serializer_context(),
            },
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def go_back(self, request, **kwargs):
        # TODO make this idempotent (e.g. include the target slot number in request)
        participation = self.get_queryset().get(pk=kwargs["pk"])
        participation.move_current_slot_cursor_back()

        current_slot = participation.current_slots[0]
        serializer = EventParticipationSlotSerializer(
            current_slot,
            context={
                EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS: True,
                **self.get_serializer_context(),
            },
        )
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

    serializer_class = EventParticipationSlotSerializer
    permission_classes = [policies.EventParticipationSlotPolicy]
    queryset = (
        EventParticipationSlot.objects.all()
        .select_related("exercise")
        .prefetch_related("sub_slots", "selected_choices")
    )

    def get_capabilities(self):
        """
        Returns a dict for usage inside serializers' context in order to decide whether
        to display some fields ans whether to make them writable
        """
        force_student = "as_student" in self.request.query_params
        has_assess_privilege = check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.ASSESS_PARTICIPATIONS,
        )
        has_manage_events_privilege = check_privilege(
            self.request.user,
            self.kwargs["course_pk"],
            privileges.MANAGE_EVENTS,
        )

        ret = {
            # assessment fields are displayed to teachers at all times and to students
            # if the assessments have been published
            "assessment_fields_read": self.get_object().participation.is_assessment_available  # accessing as student after the assessments are published
            or not force_student
            and (has_assess_privilege or has_manage_events_privilege),
            # assessment fields are writable by teachers at all times
            "assessment_fields_write": has_assess_privilege,
            "submission_fields_read": True,
            # students can access the submission fields with write privileges
            "submission_fields_write": force_student
            or not has_assess_privilege
            and not has_manage_events_privilege,
        }

        return ret

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["capabilities"] = self.get_capabilities()
        context[EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS] = True
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(participation=self.kwargs["participation_pk"])

    @action(detail=True, methods=["post"])
    def run(self, request, **kwargs):
        slot = self.get_object()
        # schedule code execution
        run_user_code_task.delay(slot.pk)
        # mark slot as running
        slot.execution_results = {
            **(slot.execution_results or {}),
            "state": "running",
        }
        slot.save(update_fields=["execution_results"])
        serializer = self.get_serializer_class()(
            slot, context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def attachment(self, request, **kwargs):
        attachment = self.get_object().attachment

        if not bool(attachment):
            return Response(status=status.HTTP_204_NO_CONTENT)

        return FileResponse(
            attachment,
            as_attachment=True,
            filename=os.path.split(attachment.name)[1],
        )
