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
            "action": ["list", "privileges"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "can_update_course",
        },
    ]

    def can_update_course(self, request, view, action):
        try:
            course_pk = request.query_params["course_id"]
        except KeyError:
            return False

        course = Course.objects.get(pk=course_pk)
        return check_privilege(request.user, course, UPDATE_COURSE)

    def is_personal_account(self, request, view, action):
        print("inside")
        user = view.get_object()
        print(user)
        return user == request.user
