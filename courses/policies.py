from rest_access_policy import AccessPolicy


class BaseAccessPolicy(AccessPolicy):
    def has_teacher_privileges(self, request, view, action, privilege):
        from courses.models import Course, CoursePrivilege

        # TODO pick the right kwarg by checking which view we're in
        course_pk = view.kwargs.get("course_pk") or view.kwargs.get("pk")

        course = Course.objects.get(pk=course_pk)
        if request.user == course.creator:
            return True

        try:
            privileges = CoursePrivilege.objects.get(
                user=request.user, course=course
            ).privileges
        except CoursePrivilege.DoesNotExist:
            return False

        return "__all__" in privileges or privilege in privileges


class CoursePolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": ["*"],
            "effect": "allow",
        },
        {
            "action": ["retrieve"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_visible_to",
        },
        {
            "action": ["create"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_teacher",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:update_course",
        },
    ]

    def is_visible_to(self, request, view, action):
        return True

    def is_teacher(self, request, view, action):
        return request.user.is_teacher


class EventPolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_course_visible_to",
        },
        {
            "action": ["create"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:create_events",  # TODO address students creating self-service practice
        },
        {
            "action": ["retrieve"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_event_visible_to",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:update_events",
        },
    ]

    def is_course_visible_to(self, request, view, action):
        return True

    def is_event_visible_to(self, request, view, action):
        return True


class EventTemplatePolicy(BaseAccessPolicy):
    # TODO implement
    pass


class ExercisePolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:access_exercises",
        },
        {
            "action": ["create"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:create_exercises",
        },
        {
            "action": ["update", "partial_update", "delete"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:modify_exercises",
        },
    ]


class EventParticipationPolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:access_participations",
        },
        {
            "action": ["retrieve"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_own_participation or has_teacher_privileges:access_participations",
        },
        {
            "action": ["create"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "can_participate",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_own_participation and can_update_participation",  # ? give teachers the ability to update participations (e.g. re-open a turned in one)
        },
    ]

    def is_own_participation(self, request, view, action):
        participation = view.get_object()
        return request.user == participation.user

    def can_participate(self, request, view, action):
        return True

    def can_update_participation(self, request, view, action):
        return True


class EventParticipationSlotPolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_in_own_participation or has_teacher_privileges:access_participations",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_in_own_participation and can_update_parent_participation or has_teacher_privileges:assess_participations",
        },
    ]

    def is_in_own_participation(self, request, view, action):
        participation = view.get_object().submission.participation
        return request.user == participation.user

    def can_update_parent_participation(self, request, view, action):
        return True
