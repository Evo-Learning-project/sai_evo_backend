from functools import lru_cache
from rest_access_policy import AccessPolicy
from courses.logic.participations import is_time_up

from courses.logic.privileges import check_privilege
from users.models import User

from .models import Course, Event, EventTemplate, Exercise, ExerciseSolution


class BaseAccessPolicy(AccessPolicy):
    NOT_ENROLLED = "NOT_ENROLLED"

    def get_course(self, view):
        from courses.models import Course
        from courses.views import CourseViewSet

        course_pk = (
            view.kwargs.get("pk")
            if isinstance(view, CourseViewSet)
            else view.kwargs.get("course_pk")  # nested view
        )

        try:
            return Course.objects.get(pk=course_pk)
        except (ValueError, Course.DoesNotExist):
            return None

    def has_teacher_privileges(self, request, view, action, privilege):
        course = self.get_course(view)
        if course is None:
            return False

        return check_privilege(request.user, course, privilege)

    def is_enrolled(self, request, view, action):
        course = self.get_course(view)
        if course is None:
            return False

        is_enrolled = request.user in course.enrolled_users.all()
        if not is_enrolled:
            self.message = self.NOT_ENROLLED
        return is_enrolled


class RequireCourseEnrollmentPolicy(BaseAccessPolicy):
    """
    A base policy that denies all requests to resources inside of a course
    if the requesting user isn't either enrolled in that course or has
    any privileges over that course.
    """

    def get_policy_statements(self, request, view):
        statements = super().get_policy_statements(request, view)
        return [
            {
                "action": ["*"],
                "principal": ["authenticated"],
                "effect": "deny",
                "condition_expression": "not has_teacher_privileges:__some__ and not is_enrolled",
            }
        ] + statements

    def is_course_creator(self, request, view, action):
        course = self.get_course(view)
        if course is None:
            return False

        return course.creator == request.user


class CoursePolicy(BaseAccessPolicy):
    statements = [
        {
            "action": [
                "list",
                "unstarted_practice_events",
                "bookmark",
                "my_enrollment",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
        },
        {
            "action": ["jobe"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:update_course",
        },
        {
            "action": ["enrollments"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_retrieve_request and has_teacher_privileges:__some__ or \
                has_teacher_privileges:update_course",
        },
        {
            "action": ["retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_visible_to",
        },
        {
            "action": ["create"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_teacher",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:update_course",
        },
        {
            "action": ["active_users", "participation_report"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:__some__",
        },
        {
            "action": ["privileges"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:update_course and \
                not target_user_is_personal_account and not target_user_is_course_creator",
        },
        {
            "action": "gamification_context",
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:update_course or \
                is_enrolled and is_retrieve_request",
        },
    ]

    def is_retrieve_request(self, request, view, action):
        return request.method == "GET"

    def is_visible_to(self, request, view, action):
        # from demo_mode.logic import is_demo_mode

        # if is_demo_mode():
        #     return is_course_accessible_in_demo_mode(view.get_object(), request.user)

        return True

    def is_teacher(self, request, view, action):
        return request.user.is_teacher

    def target_user_is_course_creator(self, request, view, action):
        try:
            user_id = request.query_params["user_id"]
            user = User.objects.get(pk=user_id)
            course = view.get_object()
            return user == course.creator
        except (KeyError, ValueError, User.DoesNotExist, Course.DoesNotExist):
            return False

    def target_user_is_personal_account(self, request, view, action):
        try:
            user_id = request.query_params["user_id"]
            user = User.objects.get(pk=user_id)
            return user == request.user
        except (KeyError, ValueError, User.DoesNotExist):
            return False


class CourseRolePolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["*"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:update_course",
        },
    ]


class EventPolicy(RequireCourseEnrollmentPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_course_visible_to and has_teacher_privileges:manage_events",
        },
        {
            "action": ["create"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "creating_self_service_practice or has_teacher_privileges:manage_events",
        },
        {
            "action": [
                "update",
                "partial_update",
                "lock",
                "unlock",
                "heartbeat",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "updating_self_service_practice and is_event_creator\
                 or has_teacher_privileges:manage_events",
        },
        {
            "action": ["instances"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:manage_events",
        },
        {
            "action": ["retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_event_visible_to",
        },
        {
            "action": ["destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_course_creator",
        },
    ]

    def creating_self_service_practice(self, request, view, action):
        try:
            return request.data["event_type"] == Event.SELF_SERVICE_PRACTICE
        except Exception:
            return False

    def updating_self_service_practice(self, request, view, action):
        event = view.get_object()
        return event.event_type == Event.SELF_SERVICE_PRACTICE

    def is_event_creator(self, request, view, action):
        event = view.get_object()
        return event.creator == request.user

    def is_course_visible_to(self, request, view, action):
        return True

    def is_event_visible_to(self, request, view, action):
        # TODO implement
        return True


class EventTemplatePolicy(RequireCourseEnrollmentPolicy):
    statements = [
        {
            "action": ["*"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_related_to_self_service_practice and is_template_event_creator\
                or has_teacher_privileges:manage_events",
        },
    ]

    def get_template(self, view):
        from courses.views import (
            EventTemplateRuleClauseViewSet,
            EventTemplateRuleViewSet,
        )

        if isinstance(view, EventTemplateRuleViewSet) or isinstance(
            view, EventTemplateRuleClauseViewSet
        ):
            try:
                template = EventTemplate.objects.get(pk=view.kwargs["template_pk"])
            except ValueError:
                return None
        else:
            template = view.get_object()

        return template

    def is_related_to_self_service_practice(self, request, view, action):
        template = self.get_template(view)
        if template is None:
            return False

        return template.event.event_type == Event.SELF_SERVICE_PRACTICE

    def is_template_event_creator(self, request, view, action):
        template = self.get_template(view)
        if template is None:
            return False

        return template.event.creator == request.user


class TagPolicy(RequireCourseEnrollmentPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
        },
    ]


class ExercisePolicy(RequireCourseEnrollmentPolicy):
    statements = [
        {
            "action": ["list", "retrieve", "bulk_get"],
            "principal": ["authenticated"],
            "effect": "allow",
            # "condition": "has_teacher_privileges:access_exercises",
        },
        {
            "action": [
                "create",
                "update",
                "partial_update",
                "destroy",
                "tags",
                "lock",
                "unlock",
                "heartbeat",
                "solution_execution_results",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:manage_exercises",
        },
    ]


class ExerciseRelatedObjectsPolicy(BaseAccessPolicy):
    # used for models related to Exercise, like ExerciseChoice,
    # ExerciseTestCase, and Exercise itself when used as a sub-exercise
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:access_exercises",
        },
        {
            "action": ["create", "update", "partial_update", "destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:manage_exercises",
        },
    ]


class EventParticipationPolicyMixin:
    NOT_IN_EVENT_ALLOWED_LIST = "NOT_IN_EVENT_ALLOWED_LIST"
    EVENT_CLOSED = "EVENT_CLOSED"
    YOU_TURNED_IN = "YOU_TURNED_IN"

    @lru_cache(maxsize=None)
    def get_participation(self, view):
        from courses.views import (
            EventParticipationSlotViewSet,
            EventParticipationViewSet,
        )

        if isinstance(view, EventParticipationViewSet):
            participation = view.get_object()
        elif isinstance(view, EventParticipationSlotViewSet):
            participation = view.get_object().participation
        else:
            assert False, f"View {view} isn't of correct type"
        return participation

    def is_own_participation(self, request, view, action):
        participation = self.get_participation(view)
        return request.user == participation.user

    def can_update_participation(self, request, view, action):
        from courses.models import Event, EventParticipation

        participation = self.get_participation(view)

        if participation.state == EventParticipation.TURNED_IN:
            self.message = self.YOU_TURNED_IN
            return False

        if participation.state == EventParticipation.CLOSED_BY_TEACHER:
            self.message = self.EVENT_CLOSED
            return False

        # check that there is time left for the participation
        if is_time_up(participation):
            return False

        event = participation.event

        event_open = event.state == Event.OPEN or (
            event.state == Event.RESTRICTED
            and request.user in event.users_allowed_past_closure.all()
        )
        if not event_open:
            self.message = self.EVENT_CLOSED

        return event_open


class EventParticipationPolicy(
    RequireCourseEnrollmentPolicy, EventParticipationPolicyMixin
):
    statements = [
        {
            "action": ["list"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:manage_events\
                or requested_own_participations",
        },
        {
            "action": ["retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_own_participation\
                or has_teacher_privileges:assess_participations",
        },
        {
            "action": ["create"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "can_participate\
                or has_teacher_privileges:manage_events",
        },
        {
            "action": ["go_back"],
            "principal": ["authenticated"],
            "effect": "deny",
            "condition_expression": "not can_go_back",
        },
        {
            "action": ["update", "partial_update", "go_forward", "go_back"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "\
                is_own_participation and \
                    (can_update_participation or is_bookmark_request)\
                or has_teacher_privileges:assess_participations",
        },
        {
            "action": ["go_forward", "go_back"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "\
                is_own_participation and can_update_participation\
                        or has_teacher_privileges:assess_participations",
        },
        {
            "action": ["bulk_patch"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "\
                has_teacher_privileges:assess_participations",
        },
        {
            "action": ["go_forward"],
            "principal": ["authenticated"],
            "effect": "deny",
            "condition_expression": "not can_go_forward",
        },
    ]

    def requested_own_participations(self, request, view, action):
        """
        The user has accessed the viewset as a sub-route of courses and hasn't
        specified a user_id in the params, therefore requesting to view their
        own participations only
        """
        return "user_id" not in request.query_params

    def can_participate(self, request, view, action):
        from courses.models import Event

        try:
            event = Event.objects.get(pk=view.kwargs["event_pk"])
        except Event.DoesNotExist:
            return True
        except (ValueError, KeyError):
            return False

        if event.state != Event.OPEN and (
            event.state != Event.RESTRICTED
            or request.user not in event.users_allowed_past_closure.all()
        ):
            self.message = self.EVENT_CLOSED
            return False

        if event.access_rule == Event.ALLOW_ACCESS:
            return request.user.email not in event.access_rule_exceptions
        else:  # default is DENY_ACCESS
            is_allowed = request.user.email in event.access_rule_exceptions
            if not is_allowed:
                self.message = self.NOT_IN_EVENT_ALLOWED_LIST
            return is_allowed

    def is_bookmark_request(self, request, view, action):
        # users are allowed to update a participation after it's
        # turned in as long as their request only involves updating
        # the `bookmarked` field
        return "bookmarked" in request.data and len(request.data.keys()) == 1

    def can_go_forward(self, request, view, action):
        participation = self.get_participation(view)  # view.get_object()
        return not participation.is_cursor_last_position

    def can_go_back(self, request, view, action):
        from courses.models import Event

        participation = self.get_participation(view)  # view.get_object()
        event = participation.event

        return not participation.is_cursor_first_position and event.allow_going_back


class EventParticipationSlotPolicy(
    RequireCourseEnrollmentPolicy, EventParticipationPolicyMixin
):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_own_participation\
                or has_teacher_privileges:assess_participations",
        },
        {
            "action": [
                "update",
                "partial_update",
                "run",
                "attachment",
                "execution_results",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "\
                is_own_participation and can_update_participation\
                    or has_teacher_privileges:assess_participations",
        },
        {
            "action": ["patch_submission"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_own_participation and can_update_participation",
        },
        {
            "action": ["retrieve", "update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "deny",
            "condition_expression": "\
                not has_teacher_privileges:assess_participations\
                and not is_slot_in_scope",
        },
    ]

    def is_slot_in_scope(self, request, view, action):
        slot = view.get_object()
        return slot.is_in_scope()


class ExerciseSolutionPolicy(RequireCourseEnrollmentPolicy):
    statements = [
        {
            "action": ["list", "retrieve", "bookmark", "vote"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_solution_visible_to_user",
        },
        {
            "action": ["destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:manage_exercise_solutions",
        },
        {
            "action": ["create", "update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:manage_exercises or \
                has_teacher_privileges:manage_exercise_solutions or \
                not is_publish_or_reject_request",
        },
        {
            "action": ["partial_update", "update"],
            "principal": ["authenticated"],
            "effect": "deny",
            "condition_expression": "not has_teacher_privileges:manage_exercises and \
                not has_teacher_privileges:manage_exercise_solutions and \
                not is_own_solution",
        },
        {
            "action": ["create", "update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "deny",
            "condition_expression": "not is_solution_visible_to_user",
        },
        {
            "action": ["vote"],
            "principal": ["authenticated"],
            "effect": "deny",
            "condition_expression": "is_own_solution",
        },
    ]

    def is_solution_visible_to_user(self, request, view, action):
        try:
            # allow access only if the requested exercise is among those for
            # which the requesting user has permission to see the solutions
            # TODO optimize (use exists() or values())

            Exercise.objects.all().with_solutions_visible_by(
                course_id=view.kwargs.get("course_pk"),
                user=request.user,
            ).get(pk=view.kwargs.get("exercise_pk"))
            return True
        except (ValueError, Exercise.DoesNotExist):
            return False

    def is_own_solution(self, request, view, action):
        solution = view.get_object()
        return request.user == solution.user

    def is_publish_or_reject_request(self, request, view, action):
        request_state = request.data.get("state", None)
        return request_state in (ExerciseSolution.PUBLISHED, ExerciseSolution.REJECTED)


class ExerciseSolutionCommentPolicy(RequireCourseEnrollmentPolicy):
    statements = [
        # TODO allow only if parent solution is visible
        {
            "action": ["create"],
            "principal": ["authenticated"],
            "effect": "allow",
        }
    ]
