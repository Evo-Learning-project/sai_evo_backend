from courses.models import Course
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User

from .serializers import UserSerializer


class UserViewSet(
    # mixins.ListModelMixin,
    # mixins.RetrieveModelMixin,
    # mixins.CreateModelMixin,
    # mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    # permission_classes = [policies.CoursePolicy]

    @action(detail=False, methods=["get"])
    def me(self, request, **kwargs):
        serializer = self.get_serializer_class()(instance=request.user)
        return Response(serializer.data)
