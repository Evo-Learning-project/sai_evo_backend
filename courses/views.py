import os

from coding.helpers import get_code_execution_results, send_jobe_request
from demo_mode.logic import is_demo_mode
from django.db import IntegrityError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User
from users.serializers import UserCreationSerializer, UserSerializer

from courses import policies
from courses.filters import (
    EventFilter,
    EventParticipationFilter,
    ExerciseFilter,
    ExerciseSolutionFilter,
)
from courses.logic.event_instances import ExercisePicker
from courses.logic.presentation import (
    CHOICE_SHOW_SCORE_FIELDS,
    COURSE_SHOW_PUBLIC_EXERCISES_COUNT,
    EVENT_PARTICIPATION_SHOW_EVENT,
    EVENT_PARTICIPATION_SHOW_SCORE,
    EVENT_PARTICIPATION_SHOW_SLOTS,
    EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS,
    EVENT_PARTICIPATION_SLOT_SHOW_EXERCISE,
    EVENT_PARTICIPATION_SLOT_SHOW_SUBMISSION_FIELDS,
    EVENT_SHOW_HIDDEN_FIELDS,
    EVENT_SHOW_PARTICIPATION_EXISTS,
    EVENT_SHOW_TEMPLATE,
    EVENT_TEMPLATE_RULE_SHOW_SATISFYING_FIELD,
    EXERCISE_SHOW_HIDDEN_FIELDS,
    EXERCISE_SHOW_SOLUTION_FIELDS,
    TAG_SHOW_PUBLIC_EXERCISES_COUNT,
    TESTCASE_SHOW_HIDDEN_FIELDS,
)
from courses.logic.privileges import (
    ACCESS_EXERCISES,
    ASSESS_PARTICIPATIONS,
    MANAGE_EVENTS,
    MANAGE_EXERCISES,
)
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
    ExerciseSolution,
    ExerciseSolutionComment,
    ExerciseSolutionVote,
    ExerciseTestCase,
    ExerciseTestCaseAttachment,
    PretotypeData,
    Tag,
    UserCoursePrivilege,
)
from courses.pagination import EventParticipationPagination, ExercisePagination
from courses.tasks import run_participation_slot_code_task

from .serializers import (
    CourseRoleSerializer,
    CourseSerializer,
    EventParticipationSerializer,
    EventParticipationSlotSerializer,
    EventParticipationSlotSubmissionSerializer,
    EventParticipationSummarySerializer,
    EventSerializer,
    EventTemplateRuleClauseSerializer,
    EventTemplateRuleSerializer,
    EventTemplateSerializer,
    ExerciseChoiceSerializer,
    ExerciseSerializer,
    ExerciseSolutionCommentSerializer,
    ExerciseSolutionSerializer,
    ExerciseSolutionVoteSerializer,
    ExerciseTestCaseAttachmentSerializer,
    ExerciseTestCaseSerializer,
    ExerciseWithSolutionsSerializer,
    PretotypeDataSerializer,
    TagSerializer,
)
from .view_mixins import (
    BulkCreateMixin,
    BulkGetMixin,
    BulkPatchMixin,
    LockableModelViewSetMixin,
    RequestingUserPrivilegesMixin,
    RestrictedListMixin,
    ScopeQuerySetByCourseMixin,
)

import logging

logger = logging.getLogger(__name__)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = (
        Course.objects.all()
        .select_related("creator")
        .prefetch_related(
            # TODO use Prefetch() to prefetch into named field that get_user_privileges expects
            # "roles",
            # "roles__users",
            # "privileged_users",
            # "privileged_users__user",
            "bookmarked_by",
        )
    )
    permission_classes = [policies.CoursePolicy]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # TODO move the exercise count to an action on the child ExerciseViewSet and have frontend do a separate call
        context[COURSE_SHOW_PUBLIC_EXERCISES_COUNT] = self.action == "retrieve"
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        # TODO use scope_queryset https://rsinger86.github.io/drf-access-policy/multi_tenacy/

        if is_demo_mode():  # !!!
            return Course.demo_manager.visible_in_demo_mode_to(self.request.user)

        if not self.request.user.is_teacher:
            qs = qs.public()

        # TODO review prefetching - previously we were prefetching for only requesting user, now what?
        # qs = qs.prefetch_related(
        #     Prefetch(
        #         "privileged_users",
        #         queryset=UserCoursePrivilege.objects.filter(user=self.request.user),
        #         to_attr="prefetched_privileged_users",
        #     ),
        #     Prefetch(
        #         "roles",
        #         queryset=self.request.user.roles.all(),
        #         to_attr="prefetched_user_roles",
        #     ),
        # )

        return qs

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def jobe(self, request, **kwargs):
        body = request.data.get("body")
        headers = request.data.get("headers")
        url = request.data.get("url")
        req_method = request.data.get("method") or "post"
        res = send_jobe_request(body, headers, req_method, url)

        return Response(res)

    @action(detail=True, methods=["put", "delete"])
    def bookmark(self, request, **kwargs):
        # TODO could possibly extract as this is shared with ExerciseSolution
        course = self.get_object()

        if self.request.method == "DELETE":
            course.bookmarked_by.remove(self.request.user)
        else:
            course.bookmarked_by.add(self.request.user)

        return Response(
            data=self.get_serializer_class()(
                self.get_object(),
                context=self.get_serializer_context(),
            ).data
        )

    @action(methods=["put", "delete"], detail=True)
    def my_enrollment(self, request, **kwargs):
        course = self.get_object()
        user_id = request.user.pk

        if request.method == "PUT":
            if request.user in course.enrolled_users.all():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "ALREADY_ENROLLED"},
                )
            course.enroll_users([user_id], bulk=False)
        else:
            if request.user not in course.enrolled_users.all():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "NOT_ENROLLED"},
                )
            course.unenroll_users([user_id])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get", "put", "delete"], detail=True)
    def enrollments(self, request, **kwargs):
        """
        An endpoint used to enroll and unenroll users to a course.
        Requires a `user_ids` or an `emails` field in the payload.

        `user_ids` can be used to enroll existing users.

        `email` can be used to enroll nonexisting users. Enrolling
        users using this option will cause their account to be created first,
        if it doesn't exist already using the email addresses in the payload.
        """
        course = self.get_object()

        if request.method == "GET":
            enrolled_users = course.enrolled_users.all()
            serializer = UserSerializer(enrolled_users, many=True)
            return Response(serializer.data)

        user_ids = request.data.get("user_ids", [])
        emails = request.data.get("emails", [])

        if not user_ids and not emails:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if len(emails) > 0 and request.method == "DELETE":
            """
            Enrollment deletion can only be performed via user id's,
            not their emails
            """
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # query for emails referring to existing accounts and retrieve
        # the corresponding user id's
        existing_users_by_email = User.objects.filter(email__in=emails).values_list(
            "id",
            "email",
        )

        # add retrieved id's to user id list
        user_ids.extend([i for (i, _) in existing_users_by_email])

        # remove emails of users that had existing accounts from the list
        # of emails to use for creating new accounts
        emails = [
            email
            for email in emails
            if email not in [e for (_, e) in existing_users_by_email]
        ]

        # create any accounts for which the email address has been given
        creation_serializer = UserCreationSerializer(
            data=[{"email": email} for email in emails], many=True
        )
        creation_serializer.is_valid(raise_exception=True)
        users = creation_serializer.save()

        try:
            if request.method == "PUT":
                course.enroll_users([*user_ids, *(u.pk for u in users)], request.user)
            else:
                course.unenroll_users(user_ids)
        except Exception as e:
            logger.error("Exception while (un)enrolling users: " + str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"])
    def privileges(self, request, **kwargs):
        """
        An endpoint used to assign course privileges to a user.
        Requires either a `user_id` or an `email` query param.

        If privileges are being assigned to a user that exists in the database, the
        `user_id` param must be used.

        If privileges are being assigned to a person who hasn't yet an account, the
        `email` param must be used, and a new account will be created with the given
        email address. Upon the person's first login, the account thus created will
        be associated to them and the permissions will already be active.

        The `email` param must not be used to retrieve an existing account.
        """
        course = self.get_object()

        params = request.query_params
        if "user_id" in params:
            user = get_object_or_404(User, pk=params["user_id"])
        elif "email" in params:
            email = params["email"]
            if User.objects.filter(email=email).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            # create a new user account from the email given as query param
            creation_serializer = UserCreationSerializer(data={"email": email})
            creation_serializer.is_valid(raise_exception=True)
            user = creation_serializer.save()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            new_privileges = request.data["course_privileges"]

            course_privileges, _ = UserCoursePrivilege.objects.get_or_create(
                user=user, course=course
            )

            # TODO probably extract this logic to a separate function, e.g. process_privilege_list
            # prevent users from having edit privileges on exercises if they don't have access to exercises
            if (
                MANAGE_EXERCISES in new_privileges
                and ACCESS_EXERCISES not in course_privileges.allow_privileges
                and ACCESS_EXERCISES not in new_privileges
            ):
                new_privileges.append(ACCESS_EXERCISES)

            # if someone is granted edit privileges on exercises, gran them access to exercises
            if ACCESS_EXERCISES not in new_privileges:
                new_privileges = [p for p in new_privileges if p != MANAGE_EXERCISES]

            course_privileges.allow_privileges = new_privileges
            course_privileges.save()
        except Exception as e:
            logger.error("Exception while setting user privileges: " + str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(
            user,
            context={"course": course},  # to include course privileges in response
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def active_users(self, request, **kwargs):
        active_users = User.objects.all().active_in_course(self.kwargs["pk"])
        serializer = UserSerializer(active_users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def participation_report(self, request, **kwargs):
        """
        Returns a report mapping all closed exams to the list of participations, showing
        the participant user id, the participation id, and the score obtained
        """
        course = self.get_object()
        exams = (
            course.events.all()
            .filter(event_type=Event.EXAM)
            .values_list("id", flat=True)
        )

        report = {
            e.hashid: EventParticipationSummarySerializer(
                EventParticipation.objects.filter(event_id=e)
                .with_prefetched_base_slots()
                .select_related("event"),
                many=True,
            ).data
            for e in exams
        }

        # TODO consider using this instead of the above for performance reasons
        # report = {
        #     e.hashid: [
        #         {
        #             "id": p.pk,
        #             "user": p.user_id,
        #             "score": p.score,
        #         }
        #         for p in EventParticipation.objects.filter(event_id=e)
        #         .with_prefetched_base_slots()
        #         .select_related("event")
        #     ]
        #     for e in exams
        # }

        return Response(report, status=status.HTTP_200_OK)

    # TODO extract query logic
    # @action(detail=True, methods=["get"])
    # def unstarted_practice_events(self, request, **kwargs):
    #     # sub-query that retrieves a user's participation to events
    #     exists_user_participation = (
    #         EventParticipation.objects.all()
    #         .with_prefetched_base_slots()
    #         .filter(user=request.user, event=OuterRef("pk"))
    #     )

    #     practice_events = Event.objects.annotate(
    #         user_participation_exists=Exists(exists_user_participation)
    #     ).filter(
    #         creator=request.user,
    #         course=self.get_object(),
    #         event_type=Event.SELF_SERVICE_PRACTICE,
    #         user_participation_exists=False,
    #     )

    #     return EventSerializer(practice_events, many=True, context=self.context).data

    @action(methods=["get", "post"], detail=True)
    def gamification_context(self, request, **kwargs):
        from django.contrib.contenttypes.models import ContentType
        from gamification.models import GamificationContext
        from gamification.serializers import GamificationContextSerializer

        # TODO refactor
        course = self.get_object()

        object_content_type = ContentType.objects.get_for_model(course)

        if request.method == "GET":
            gamification_context = get_object_or_404(
                GamificationContext.objects.all(),
                content_type=object_content_type,
                object_id=course.pk,
            )
        else:
            gamification_context = GamificationContext.objects.get_or_create(
                content_type=object_content_type,
                object_id=course.pk,
            )

        serializer = GamificationContextSerializer(
            gamification_context, context={"request": request}
        )
        return Response(serializer.data)


class CourseRoleViewSet(ScopeQuerySetByCourseMixin):
    serializer_class = CourseRoleSerializer
    queryset = CourseRole.objects.all()
    permission_classes = [policies.CourseRolePolicy]

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


class ExerciseSolutionViewSet(
    viewsets.ModelViewSet,
    RestrictedListMixin,
    RequestingUserPrivilegesMixin,
):
    serializer_class = ExerciseSolutionSerializer
    queryset = (
        ExerciseSolution.objects.all()
        .with_prefetched_related_objects()
        .order_by_published_first()
        .order_by_score_descending()
    )
    permission_classes = [policies.ExerciseSolutionPolicy]
    pagination_class = ExercisePagination
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = ExerciseSolutionFilter

    def perform_create(self, serializer):
        serializer.save(
            exercise_id=self.kwargs.get("exercise_pk"),
            user=self.request.user,
        )

    def get_queryset(self):
        qs = super().get_queryset()

        if self.kwargs.get("exercise_pk") is not None:
            # using the viewset as sub-route of exercises/
            qs = qs.filter(exercise_id=self.kwargs["exercise_pk"])
        else:
            # getting all the solutions for all exercises of a course
            # i.e. sub-route of courses/
            qs = qs.filter(
                exercise__course_id=self.kwargs["course_pk"]
            ).with_prefetched_exercise_and_related_objects()

        # don't show solutions for non-public exercises to unprivileged users
        if MANAGE_EXERCISES in self.user_privileges:
            qs = qs.exclude_draft_unless_authored_by(
                self.request.user  # only show DRAFT solutions to their authors
            )
        else:
            # TODO is .visible_by(course_id=self.kwargs["course_pk"], user=self.request.user) necessary?
            qs = qs.exclude_draft_and_rejected_unless_authored_by(
                self.request.user  # only show DRAFT and REJECTED solutions to their authors
            )

        return qs.prefetch_related("comments", "votes")

    @action(methods=["put", "delete"], detail=True)
    def bookmark(self, *args, **kwargs):
        solution = self.get_object()

        if self.request.method == "DELETE":
            solution.bookmarked_by.remove(self.request.user)
        else:
            solution.bookmarked_by.add(self.request.user)

        return Response(
            data=self.get_serializer_class()(
                self.get_object(),
                context=self.get_serializer_context(),
            ).data
        )

    @action(methods=["put", "delete"], detail=True)
    def vote(self, *args, **kwargs):
        solution = self.get_object()

        if self.request.method == "DELETE":
            # delete user's vote
            my_vote = get_object_or_404(solution.votes.all(), user=self.request.user)
            my_vote.delete()
        else:
            # TODO double check
            # create or update user's vote
            try:
                serializer_arg = [
                    ExerciseSolutionVote.objects.get(
                        solution=solution,
                        user=self.request.user,
                    )
                ]
            except ExerciseSolutionVote.DoesNotExist:
                serializer_arg = []
            serializer = ExerciseSolutionVoteSerializer(
                *serializer_arg,
                data={
                    **self.request.data,
                },
            )
            serializer.is_valid()
            serializer.save(
                **{
                    "solution_id": solution.pk,
                    "user": self.request.user,
                }
            )

        return Response(
            data=self.get_serializer_class()(
                self.get_object(),
                context=self.get_serializer_context(),
            ).data
        )

    @action(methods=["get"], detail=False)
    def popular(self, *args, **kwargs):
        qs = self.get_queryset()  # TODO create popular qs method
        return self.restricted_list(qs)

    @action(methods=["get"], detail=False)
    def submitted(self, *args, **kwargs):
        qs = self.get_queryset().filter(state=ExerciseSolution.SUBMITTED)
        return self.restricted_list(qs)

    @action(detail=True, methods=["post"])
    def execution_results(self, request, **kwargs):
        # TODO make async
        solution: ExerciseSolution = self.get_object()
        results = get_code_execution_results(
            exercise=solution.exercise,
            code=solution.content,
        )
        return Response(results)


class ExerciseSolutionCommentViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSolutionCommentSerializer
    queryset = ExerciseSolutionComment.objects.all()
    permission_classes = [policies.ExerciseSolutionCommentPolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(solution_id=self.kwargs["solution_pk"])

    def perform_create(self, serializer):
        serializer.save(
            solution_id=self.kwargs.get("solution_pk"),
            user=self.request.user,
        )


class ExerciseViewSet(
    BulkCreateMixin,
    ScopeQuerySetByCourseMixin,
    BulkGetMixin,
    RequestingUserPrivilegesMixin,
    LockableModelViewSetMixin,
):
    serializer_class = ExerciseSerializer
    queryset = Exercise.objects.all().with_prefetched_related_objects()
    permission_classes = [policies.ExercisePolicy]
    pagination_class = ExercisePagination
    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
    ]
    filterset_class = ExerciseFilter
    search_fields = ["label", "text"]

    def get_permissions(self):
        if self.kwargs.get("exercise_pk"):
            # accessing a sub-exercise
            self.permission_classes = [policies.ExerciseRelatedObjectsPolicy]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "export":
            return ExerciseWithSolutionsSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context[EXERCISE_SHOW_SOLUTION_FIELDS] = (
            MANAGE_EXERCISES in self.user_privileges
            or ACCESS_EXERCISES in self.user_privileges
        )
        context[EXERCISE_SHOW_HIDDEN_FIELDS] = (
            MANAGE_EXERCISES in self.user_privileges
            or ACCESS_EXERCISES in self.user_privileges
        )
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        if self.kwargs.get("exercise_pk") is not None:
            # using the viewset for sub-exercises
            qs = qs.filter(parent_id=self.kwargs["exercise_pk"])
        elif self.action == "list":
            qs = qs.base_exercises()

        # restrict qs to exercises the requesting user has permission to see
        return qs.visible_by(course_id=self.kwargs["course_pk"], user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            parent_id=self.kwargs.get("exercise_pk"),
            creator=self.request.user,
        )

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
            # TODO validate text through serializer
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
        # TODO this is temporary, find a more robust solution
        solutions = exercise.solutions.filter(state=ExerciseSolution.PUBLISHED)
        res = {}
        for solution in solutions:
            res[solution.pk] = get_code_execution_results(
                exercise=exercise,
                code=solution.content,
            )
        return Response(res)

    @action(detail=False, methods=["get"])
    def export(self, request, **kwargs):
        return self.list(request, **kwargs)


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
        """ TODO 
        check if you can do /courses/i/exercises/n/choices where n isn't an exercises of course i and 
        it'll still work; if so, fix it, probably by also filtering by exercise__course_id 
        """
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


class ExerciseTestCaseAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseTestCaseAttachmentSerializer
    queryset = ExerciseTestCaseAttachment.objects.all()
    permission_classes = [policies.ExerciseRelatedObjectsPolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(testcase_id=self.kwargs["testcase_pk"])

    def perform_create(self, serializer):
        serializer.save(
            testcase_id=self.kwargs["testcase_pk"],
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieving an ExerciseTestCaseAttachment downloads
        the attached file
        """
        attachment = self.get_object().attachment

        if not bool(attachment):
            return Response(status=status.HTTP_204_NO_CONTENT)

        return FileResponse(
            attachment,
            as_attachment=True,
            filename=os.path.split(attachment.name)[1],
        )


class TagViewSet(
    RequestingUserPrivilegesMixin,
    ScopeQuerySetByCourseMixin,
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [policies.TagPolicy]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.with_prefetched_public_exercises().with_prefetched_public_unseen_exercises(
            self.request.user
        )

        # students can only access public tags
        if MANAGE_EXERCISES not in self.user_privileges:
            # TODO use scope_queryset
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


class EventViewSet(
    ScopeQuerySetByCourseMixin, RequestingUserPrivilegesMixin, LockableModelViewSetMixin
):
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
    permission_classes = [policies.EventPolicy]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter

    def get_queryset(self):
        qs = super().get_queryset()
        if MANAGE_EVENTS not in self.user_privileges:
            # TODO double check whether we should exclude other states as well
            qs = qs.exclude(_event_state=Event.DRAFT)
            if self.action == "list":
                qs = qs.filter(visibility=Event.PUBLIC)

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # show hidden fields only to privileged users
        context[EVENT_SHOW_HIDDEN_FIELDS] = MANAGE_EVENTS in self.user_privileges
        context[EVENT_TEMPLATE_RULE_SHOW_SATISFYING_FIELD] = (
            MANAGE_EVENTS in self.user_privileges
            and "include_event_template_rule_details" in self.request.query_params
        )
        # tell user if a participation of their own to the
        # event exists if they retrieve a specific event
        context[EVENT_SHOW_PARTICIPATION_EXISTS] = self.action == "retrieve"
        # don't show events' templates if they are shown in
        # a list in order to save queries
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
                    [e for e, _ in ExercisePicker().get_exercises_from(template)],
                    many=True,
                ).data
                # TODO? context to exercise serializer?
            )

        return Response(data)


# TODO disallow actions and make read-only
class EventTemplateViewSet(ScopeQuerySetByCourseMixin):
    serializer_class = EventTemplateSerializer
    queryset = EventTemplate.objects.all()
    permission_classes = [policies.EventTemplatePolicy]

    def perform_create(self, serializer):
        serializer.save(
            course_id=self.kwargs["course_pk"],
            creator=self.request.user,
        )


class EventTemplateRuleViewSet(viewsets.ModelViewSet, RequestingUserPrivilegesMixin):
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
        context[EVENT_TEMPLATE_RULE_SHOW_SATISFYING_FIELD] = (
            MANAGE_EXERCISES in self.user_privileges
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            template_id=self.kwargs["template_pk"],
            search_public_tags_only=(
                # if rule was created by a student, rule should only search for public tags
                MANAGE_EXERCISES
                not in self.user_privileges
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
    BulkPatchMixin,
    RequestingUserPrivilegesMixin,
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
        .order_by("-begin_timestamp")
        .with_prefetched_base_slots()
        # .select_related("event__course__googleclassroomcoursetwin")
    )
    permission_classes = [policies.EventParticipationPolicy]
    serializer_class = EventParticipationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventParticipationFilter

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context[EVENT_PARTICIPATION_SHOW_SLOTS] = True

        if self.action == "retrieve":
            # if a participation to a practice is being retrieved, or the assessments
            # for the participation are available, show solution fields
            participation = self.get_object()
            show_assessments_and_solutions = (
                participation.event.event_type == Event.SELF_SERVICE_PRACTICE
                or participation.is_assessment_available
            )
            context[EVENT_PARTICIPATION_SHOW_SCORE] = show_assessments_and_solutions
            context[EXERCISE_SHOW_SOLUTION_FIELDS] = show_assessments_and_solutions

        # show "computationally expensive" fields only if accessing a single
        # participation or explicitly requesting them in query params
        if self.action != "list" or "include_details" in self.request.query_params:
            context[EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS] = True
            context[EVENT_PARTICIPATION_SLOT_SHOW_EXERCISE] = True
            context[EVENT_PARTICIPATION_SLOT_SHOW_SUBMISSION_FIELDS] = True

        # downloading for csv, do processing on answer text
        if "for_csv" in self.request.query_params:
            context["trim_images_in_text"] = True

        # always show solution and exercises' hidden fields to teachers
        if MANAGE_EVENTS in self.user_privileges:
            context[EXERCISE_SHOW_HIDDEN_FIELDS] = True
            context[EXERCISE_SHOW_SOLUTION_FIELDS] = True

        if self.action != "list" or "include_event" in self.request.query_params:
            context[EVENT_PARTICIPATION_SHOW_EVENT] = True

        context["capabilities"] = self.get_capabilities()
        return context

    def get_capabilities(self):
        """
        Returns a dict for usage inside serializers' context in order to decide whether
        to display some fields ans whether to make them writable
        """
        # TODO improve this by checking for truthy values (use a generic solution to parse query params)
        force_student = "as_student" in self.request.query_params
        has_assess_privilege = ASSESS_PARTICIPATIONS in self.user_privileges
        has_manage_events_privilege = MANAGE_EVENTS in self.user_privileges

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

    @property
    def paginator(self):
        """
        Paginate action `list` if accessing as a sub-route of courses
        """
        if (
            self.action == "list"
            and self.kwargs.get("event_pk") is None
            and self.request.query_params.get("user_id") is None
            and not hasattr(self, "_paginator")
        ):
            self._paginator = EventParticipationPagination()
        return super().paginator

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

                if "include_event" in self.request.query_params:
                    qs = qs.prefetch_related("event__template__rules")
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
            except IntegrityError:  # race condition detected
                logger.error("race condition detected for user " + str(request.user))
                return self.create(request, *args, **kwargs)
            except Event.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer_class()(
            participation, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    # TODO FIXME this action and go_back should NOT prefetch all the related objects to base slots
    @action(detail=True, methods=["post"])
    def go_forward(self, request, **kwargs):
        # TODO make this idempotent (e.g. include the target slot number in request) or add a few seconds throttle
        # participation = self.get_queryset().get(pk=kwargs["pk"])
        participation = self.get_object()
        participation.move_current_slot_cursor_forward()

        current_slot = participation.current_slots[0]
        serializer = EventParticipationSlotSerializer(
            current_slot,
            context={
                EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS: True,
                EVENT_PARTICIPATION_SLOT_SHOW_EXERCISE: True,
                EVENT_PARTICIPATION_SLOT_SHOW_SUBMISSION_FIELDS: True,
                **self.get_serializer_context(),
            },
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def go_back(self, request, **kwargs):
        # TODO make this idempotent (e.g. include the target slot number in request)
        # participation = self.get_queryset().get(pk=kwargs["pk"])
        participation = self.get_object()
        participation.move_current_slot_cursor_back()

        current_slot = participation.current_slots[0]
        serializer = EventParticipationSlotSerializer(
            current_slot,
            context={
                EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS: True,
                EVENT_PARTICIPATION_SLOT_SHOW_EXERCISE: True,
                EVENT_PARTICIPATION_SLOT_SHOW_SUBMISSION_FIELDS: True,
                **self.get_serializer_context(),
            },
        )
        return Response(serializer.data)


class EventParticipationSlotViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    RequestingUserPrivilegesMixin,
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
        .select_related("participation", "exercise")
        .prefetch_related("selected_choices")
    )  # TODO FIXME optimize is_in_scope (no prefetching of base slots)

    def get_capabilities(self):
        """
        Returns a dict for usage inside serializers' context in order to decide whether
        to display some fields ans whether to make them writable
        """
        # TODO improve this by checking for truthy values
        force_student = "as_student" in self.request.query_params or self.action in (
            "patch_submission",
            "run",
        )
        has_assess_privilege = ASSESS_PARTICIPATIONS in self.user_privileges
        has_manage_events_privilege = MANAGE_EVENTS in self.user_privileges

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
            # TODO this is hacky - only allow writing using the patch_submission endpoint
            "submission_fields_write": force_student
            or not has_assess_privilege
            and not has_manage_events_privilege,
        }

        return ret

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["capabilities"] = self.get_capabilities()
        context[EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS] = True
        context[EVENT_PARTICIPATION_SLOT_SHOW_EXERCISE] = True
        context[EVENT_PARTICIPATION_SLOT_SHOW_SUBMISSION_FIELDS] = True
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        # TODO add ability to filter by exercise to get usages of an exercise
        return (
            qs.filter(participation=self.kwargs["participation_pk"])
            .select_related("exercise", "participation", "participation__event")
            .prefetch_related("sub_slots", "selected_choices")
        )

    def get_serializer_class(self):
        if self.action in ("patch_submission", "run"):
            return EventParticipationSlotSubmissionSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=["patch"])
    def patch_submission(self, request, **kwargs):
        """
        Endpoint for updating the submission of a slot - this is preferred over a
        regular PATCH request because the only fields that can be updated are the
        ones related to the submission
        """
        return self.partial_update(request, **kwargs)

    @action(detail=True, methods=["post"])
    def run(self, request, **kwargs):
        slot = self.get_object()
        try:
            # mark slot as running
            slot.execution_results = {
                **(slot.execution_results or {}),
                "state": "running",
            }
            slot.save(update_fields=["execution_results"])

            # schedule code execution
            run_participation_slot_code_task.delay(slot.pk)
        except Exception as e:
            logger.critical("Exception in run action " + str(e))
            slot.execution_results = {
                **(slot.execution_results or {}),
                "state": "internal_error",
            }
            slot.save(update_fields=["execution_results"])

        serializer = self.get_serializer_class()(
            self.get_object(),
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def execution_results(self, request, **kwargs):
        slot = self.get_object()
        return Response(slot.execution_results, status=status.HTTP_200_OK)

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


class PretotypeDataCreationViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = PretotypeDataSerializer
    queryset = PretotypeData.objects.all()

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)
