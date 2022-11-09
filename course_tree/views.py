from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import CourseTreeNodePolymorphicSerializer
from .models import Course, BaseCourseTreeNode, RootCourseTreeNode


class TreeNodeViewSet(viewsets.ModelViewSet):
    serializer_class = CourseTreeNodePolymorphicSerializer
    queryset = BaseCourseTreeNode.objects.all()
    # TODO permissions

    def get_queryset(self):
        qs = super().get_queryset()
        if self.kwargs.get("parent_pk") is not None:
            # using the viewset as a sub-route to get the children of a node
            qs = qs.filter(parent_id=self.kwargs["parent_pk"])
        return qs

    @action(detail=False, methods=["get"])
    def root_for_course(self, request, **kwargs):
        try:
            course_id = request.query_params["course_id"]
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            # TODO this assumes there's only one tree per course, keep an eye on it
            root = get_object_or_404(RootCourseTreeNode, course_id=course_id)
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(root)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def move(self, request, **kwargs):
        params = request.query_params
        node = self.get_object()

        target_id = params.get("target")
        position = params.get("position")

        if target_id is None or position is None:
            return Response(status=400)

        target = get_object_or_404(BaseCourseTreeNode, pk=target_id)

        node.move_to(target=target, position=position)

        return Response(status=200)
