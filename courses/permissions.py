from rest_framework import permissions

from courses.models import Course


class TeachersOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            # deny access to unauthenticated users
            return False

        course = Course.objects.get(pk=view.kwargs["course_pk"])
        return request.user.has_teacher_privileges(course)


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

        if view.action in ["retrieve", "partial_update"]:
            # students can only retrieve and modify their participations
            return obj.user == request.user


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
