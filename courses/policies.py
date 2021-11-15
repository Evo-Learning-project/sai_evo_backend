class BaseAccessPolicy(AccessPolicy):
    def has_teacher_privileges(request, view, action, privilege):
        from courses.models import Course

        course = Course.objects.get(pk=view.kwargs["course_pk"])
        if request.user == course.creator:
            return True

        try:
            privileges = None  # TODO get privilege model
        except Exception:  # TODO use appropriate exception
            return False

        return "__all__" in privileges or privilege in privileges


class EventParticipationPolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "has_teacher_privileges:access_events_participations",
        },
        {
            "action": ["retrieve"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_own_participation or has_teacher_privileges:access_events_participations",
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
            "condition": "is_own_participation",
        },
    ]


class EventParticipationSlotPolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_in_own_participation or has_teacher_privileges:access_events_participations",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_in_own_participation and can_update_parent_participation or has_teacher_privileges:assess_participations",
        },
    ]


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
