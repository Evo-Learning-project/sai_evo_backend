from rest_access_policy import AccessPolicy
from courses.logic.privileges import check_privilege, UPDATE_COURSE
from gamification.models import GamificationContext

import logging

logger = logging.getLogger(__name__)


class BaseGamificationAccessPolicy(AccessPolicy):
    def has_update_privileges_on_context_course(self, request, view, action):
        from courses.models import Course
        from .views import CourseGamificationContextViewSet

        try:
            context = (
                view.get_object()
                if isinstance(view, CourseGamificationContextViewSet)
                else GamificationContext.objects.get(pk=view.kwargs.get("context_pk"))
            )

            course = context.content_object

            assert isinstance(
                course, Course
            ), "GamificationContext can currently only be associated to a Course"
        except Exception as e:
            logger.error("Exception in has_teacher_privileges_on_context: " + str(e))
            return False

        return check_privilege(request.user, course, UPDATE_COURSE)


class GamificationContextAccessPolicy(BaseGamificationAccessPolicy):
    statements = [
        {
            "action": ["leaderboard"],
            "principal": ["authenticated"],
            "effect": "allow",
        },
        {
            "action": [""],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:update_course and \
                not is_personal_account and not is_course_creator",
        },
    ]

    def is_visible_to(self, request, view, action):
        from demo_mode.logic import is_demo_mode
