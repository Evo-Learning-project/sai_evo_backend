from rest_framework import permissions

from courses.models import Course


class TeacherPrivilegesOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.has_teacher_privileges(obj)


class TeacherPrivilegesOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.has_teacher_privileges(obj):
            return True

        return request.method in permissions.SAFE_METHODS


class EventVisibilityPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.is_visible_to(request.user)


class EventParticipationPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            # deny access to unauthenticated users
            return False

        if view.action in ["list", "retrieve", "create", "partial_update"]:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.has_teacher_privileges(obj.event.course):
            # teachers can access all participations
            return True

        if view.action == "create":
            return request.user.can_participate(obj.event)

        if view.action in ["retrieve", "partial_update"]:
            # students can only retrieve and modify their participations and
            # only if they're allowed to do so (e.g. the event isn't closed)
            return obj.user == request.user and request.user.can_update_participation(
                obj
            )


class EventParticipationSlotPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            # deny access to unauthenticated users
            return False

        if view.action in ["list", "retrieve", "partial_update"]:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.has_teacher_privileges(obj.event.course):
            # teachers can access all slots
            return True

        if view.action in ["retrieve", "partial_update"]:
            # students can only retrieve and modify their participations
            return obj.participation.user == request.user