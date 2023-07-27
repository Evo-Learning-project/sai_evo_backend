from rest_access_policy import AccessPolicy
from course_tree.models import AnnouncementNode, LessonNode
from courses.logic.privileges import (
    ASSESS_PARTICIPATIONS,
    UPDATE_COURSE,
    check_privilege,
)

from courses.models import Course, Event


class GoogleClassroomAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["oauth2_callback"],
            "principal": ["*"],
            "effect": "allow",
        },
        {
            "action": [
                "authorized_scopes",
                "auth_url",
                "classroom_courses",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
        },
        {
            "action": ["course"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_course_integration_request_allowed",
        },
        {
            "action": ["coursework"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "can_access_exam_twin",
        },
        {
            "action": ["material"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "can_access_material_twin",
        },
        {
            "action": ["announcement"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "can_access_announcement_twin",
        },
        {
            "action": ["sync_exam_grades"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "can_sync_exam_grades",
        },
        {
            "action": ["sync_course_roster"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "can_sync_course_roster",
        },
    ]

    def is_course_integration_request_allowed(self, request, view, action):
        try:
            course = Course.objects.get(pk=request.query_params["course_id"])
        except:
            return False

        if course.creator == request.user:
            return True

        if (
            check_privilege(request.user, course, "__some__")
            and request.method == "GET"
        ):
            return True

        return False

    def can_access_exam_twin(self, request, view, action):
        try:
            event = Event.objects.get(pk=view.kwargs["event_id"])
            course = event.course
        except:
            return False

        return check_privilege(request.user, course, "__some__")

    def can_access_material_twin(self, request, view, action):
        try:
            lesson = LessonNode.objects.get(pk=view.kwargs["lesson_id"])
            course = lesson.get_course()
        except:
            return False

        return check_privilege(request.user, course, "__some__")

    def can_access_announcement_twin(self, request, view, action):
        try:
            announcement = AnnouncementNode.objects.get(
                pk=view.kwargs["announcement_id"]
            )
            course = announcement.get_course()
        except:
            return False

        return check_privilege(request.user, course, "__some__")

    def can_sync_exam_grades(self, request, view, action):
        try:
            event = Event.objects.get(pk=view.kwargs["event_id"])
            course = event.course
        except:
            return False

        return check_privilege(request.user, course, ASSESS_PARTICIPATIONS)

    def can_sync_course_roster(self, request, view, action):
        try:
            course = Course.objects.get(pk=request.query_params["course_id"])
        except:
            return False

        return check_privilege(request.user, course, UPDATE_COURSE)
