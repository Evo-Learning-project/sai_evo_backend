from functools import cached_property
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from courses.abstract_models import LockableModel

from courses.logic.privileges import get_user_privileges
from rest_framework.decorators import action
from rest_framework.response import Response

from courses.models import Course


class LockableModelViewSetMixin:
    @action(detail=True, methods=["post"])
    def lock(self, request, **kwargs):
        obj: LockableModel = self.get_object()
        success = obj.try_lock(request.user)

        if not success:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return self.retrieve(request, **kwargs)

    @action(detail=True, methods=["post"])
    def unlock(self, request, **kwargs):
        obj: LockableModel = self.get_object()
        obj.unlock_or_give_up(request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def heartbeat(self, request, **kwargs):
        obj: LockableModel = self.get_object()
        success = obj.heartbeat(request.user)
        status_code = (
            status.HTTP_204_NO_CONTENT if success else status.HTTP_403_FORBIDDEN
        )

        return Response(status=status_code)


class RequestingUserPrivilegesMixin:
    @cached_property
    def user_privileges(self):
        return get_user_privileges(
            self.request.user,
            self.kwargs["course_pk"],
        )


class RestrictedListMixin:
    def restricted_list(self, qs):
        serializer = self.get_serializer_class()(
            qs,
            context=self.get_serializer_context(),
            many=True,
        )
        return Response(serializer.data)


class BulkCreateMixin:
    # @transaction.atomic()
    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)


class BulkPatchMixin:
    # @transaction.atomic()
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


"""
TODO create serializer to support bulk update 
(https://www.django-rest-framework.org/api-guide/serializers/#listserializer) and 
then in the above use:
      serializer_data = [{"id": p, **data} for p in id_list]
        serializer = self.get_serializer_class()(
            self.get_queryset().filter(id__in=id_list),
            data=serializer_data,
            many=True,
            context=self.get_serializer_context(),
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)
"""


class BulkGetMixin:
    @action(detail=False, methods=["get"])
    def bulk_get(self, request, **kwargs):
        try:
            ids = request.query_params["ids"]
            id_list = ids.split(",")
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        items = []
        try:
            course = get_object_or_404(Course, pk=self.kwargs["course_pk"])

            for pk in id_list:
                item = get_object_or_404(self.get_queryset(), pk=pk)
                items.append(item)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_class()(
            data=items,
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
        try:
            return qs.filter(course_id=self.kwargs["course_pk"])
        except ValueError:  # invalid value for course_pk
            raise Http404
