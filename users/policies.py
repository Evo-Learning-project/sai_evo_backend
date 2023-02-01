from courses.logic.privileges import UPDATE_COURSE, check_privilege
from courses.models import Course
from rest_access_policy import AccessPolicy


class UserPolicy(AccessPolicy):
    statements = [
        {
            "action": ["me"],
            "principal": ["authenticated"],
            "effect": "allow",
        },
        {
            "action": ["partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_personal_account",
        },
        {
            "action": ["list"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_some_privilege_over_course",
        },
        {
            "action": ["privileges"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "can_update_course and not is_personal_account",
        },
    ]

    def can_update_course(self, request, view, action):
        try:
            course_pk = request.query_params["course_id"]
        except KeyError:
            return False

        course = Course.objects.get(pk=course_pk)
        return check_privilege(request.user, course, UPDATE_COURSE)

    def has_some_privilege_over_course(self, request, view, action):
        try:
            course_pk = request.query_params["course_id"]
        except KeyError:
            return False

        course = Course.objects.get(pk=course_pk)
        return check_privilege(request.user, course, "__some__")

    def is_personal_account(self, request, view, action):
        user = view.get_object()
        return user == request.user
