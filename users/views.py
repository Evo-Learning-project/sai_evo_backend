from courses.models import Course, UserCoursePrivilege
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User

from .serializers import UserSerializer


class UserViewSet(
    mixins.ListModelMixin,
    # mixins.RetrieveModelMixin,
    # mixins.CreateModelMixin,
    # mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    # TODO check user is a teacher
    # permission_classes = [policies.CoursePolicy]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        params = context["request"].query_params
        if "course_id" in params:
            # TODO check user is allowed to see permissions for this course
            course = get_object_or_404(Course, pk=params["course_id"])
            context["course"] = course
        return context

    @action(detail=False, methods=["get"])
    def me(self, request, **kwargs):
        serializer = self.get_serializer_class()(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def privileges(self, request, **kwargs):
        params = request.query_params
        if "course_id" in params:
            # TODO check user is allowed to see permissions for this course
            course = get_object_or_404(Course, pk=params["course_id"])
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = self.get_object()

        try:
            new_privileges = request.data["course_privileges"]

            course_privileges, _ = UserCoursePrivilege.objects.get_or_create(
                user=user, course=course
            )
            course_privileges.allow_privileges = new_privileges
            course_privileges.save()
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        return Response(serializer.data)
