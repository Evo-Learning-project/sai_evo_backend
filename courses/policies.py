from functools import lru_cache
from rest_access_policy import AccessPolicy
from courses.logic.participations import is_time_up

from courses.logic.privileges import check_privilege
from users.models import User

from .models import Course, Event, EventTemplate, Exercise, ExerciseSolution


class BaseAccessPolicy(AccessPolicy):
    def has_teacher_privileges(self, request, view, action, privilege):
        from courses.models import Course
        from courses.views import CourseViewSet

        course_pk = (
            view.kwargs.get("pk")
            if isinstance(view, CourseViewSet)
            else view.kwargs.get("course_pk")  # nested view
        )

        try:
            course = Course.objects.get(pk=course_pk)
        except (ValueError, Course.DoesNotExist):
            return False

        return check_privilege(request.user, course, privilege)


class CoursePolicy(BaseAccessPolicy):
    statements = [
        {
            "action": [
                "list",
                "unstarted_practice_events",
                "gamification_context",
                "bookmark",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
        },
        {
            "action": ["set_permissions", "jobe"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:update_course",
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
            "action": ["active_users"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:__some__",
        },
        {
            "action": ["privileges"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:update_course and \
                not is_personal_account and not is_course_creator",
        },
    ]

    def is_visible_to(self, request, view, action):
        from demo_mode.logic import is_demo_mode

        # if is_demo_mode():
        #     return is_course_accessible_in_demo_mode(view.get_object(), request.user)

        return True

    def is_teacher(self, request, view, action):
        return request.user.is_teacher

    def is_course_creator(self, request, view, action):
        try:
            user_id = request.query_params["user_id"]
            user = User.objects.get(pk=user_id)
            course = view.get_object()
            return user == course.creator
        except (KeyError, ValueError, User.DoesNotExist, Course.DoesNotExist):
            return False

    def is_personal_account(self, request, view, action):
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


class EventPolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_course_visible_to and has_teacher_privileges:manage_events",
        },
        # TODO for creation you just need to check those conditions, for updating etc. you also need to check event creator
        {
            "action": [
                "create",
                "update",
                "partial_update",
                "lock",
                "unlock",
                "heartbeat",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_self_service_practice or has_teacher_privileges:manage_events",
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
    ]

    def is_self_service_practice(self, request, view, action):
        try:
            # TODO distinguish by action: in update, you need to check type is *already* a practice
            return request.data["event_type"] == Event.SELF_SERVICE_PRACTICE
        except Exception:
            return False

    def is_course_visible_to(self, request, view, action):
        return True

    def is_event_visible_to(self, request, view, action):
        # TODO implement
        return True


class EventTemplatePolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["*"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_related_to_self_service_practice or has_teacher_privileges:manage_events",
        },
    ]

    def is_related_to_self_service_practice(self, request, view, action):
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
                return False
        else:
            template = view.get_object()

        # TODO you also need to check the creator
        return template.event.event_type == Event.SELF_SERVICE_PRACTICE


class TagPolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
        },
    ]


class ExercisePolicy(BaseAccessPolicy):
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
            return False

        # check that there is time left for the participation
        if is_time_up(participation):
            return False

        event = participation.event

        return event.state == Event.OPEN or (
            event.state == Event.RESTRICTED
            and request.user in event.users_allowed_past_closure.all()
        )


class EventParticipationPolicy(BaseAccessPolicy, EventParticipationPolicyMixin):
    NOT_IN_EVENT_ALLOWED_LIST = "NOT_IN_EVENT_ALLOWED_LIST"
    EVENT_CLOSED = "EVENT_CLOSED"
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


class EventParticipationSlotPolicy(BaseAccessPolicy, EventParticipationPolicyMixin):
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


class ExerciseSolutionPolicy(BaseAccessPolicy):
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


class ExerciseSolutionCommentPolicy(BaseAccessPolicy):
    statements = [
        # TODO allow only if parent solution is visible
        {
            "action": ["create"],
            "principal": ["authenticated"],
            "effect": "allow",
        }
    ]
