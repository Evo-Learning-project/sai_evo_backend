from courses.logic.privileges import UPDATE_COURSE, check_privilege
from courses.models import Course
from rest_access_policy import AccessPolicy


class UserPolicy(AccessPolicy):
    statements = [
        {
            "action": ["me"],
            "principal": ["*"],
            "effect": "allow",
        },
        {
            "action": ["list", "privileges"],
            "principal": ["*"],
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
