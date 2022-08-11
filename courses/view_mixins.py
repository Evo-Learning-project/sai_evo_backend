from functools import cached_property
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets

from courses.logic.privileges import get_user_privileges
from rest_framework.decorators import action
from rest_framework.response import Response

from courses.models import Course


class RequestingUserPrivilegesMixin:
    @cached_property
    def user_privileges(self):
        return get_user_privileges(
            self.request.user,
            self.kwargs["course_pk"],
        )


class BulkCreateMixin:
    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)


class BulkPatchMixin:
    @action(detail=False, methods=["patch"])
    def bulk_patch(self, request, **kwargs):
        try:
            ids = request.query_params["ids"]
            id_list = ids.split(",")
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        ret = []

        try:
            for pk in id_list:
                participation = get_object_or_404(self.get_queryset(), pk=pk)
                ret.append(participation)

                serializer = self.get_serializer_class()(
                    participation,
                    context=self.get_serializer_context(),
                    data=data,
                    partial=True,
                )
                serializer.is_valid()
                serializer.save()
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_class()(
            ret,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class BulkGetMixin:
    @action(detail=False, methods=["get"])
    def bulk_get(self, request, **kwargs):
        try:
            ids = request.query_params["ids"]
            id_list = ids.split(",")
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        exercises = []
        try:
            course = get_object_or_404(Course, pk=self.kwargs["course_pk"])

            for pk in id_list:
                exercise = get_object_or_404(self.get_queryset(), pk=pk)
                exercises.append(exercise)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_class()(
            data=exercises,
            many=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid()
        return Response(serializer.data)


class ScopeQuerySetByCourseMixin(viewsets.ModelViewSet):
    """
    Filters its queryset by the course_pk
    kwarg. Used by all sub-routes of /courses/<course_pk> to get
    the appropriate querysets
    """

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(course_id=self.kwargs["course_pk"])
