import os
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from course_tree.filters import CourseTreeNodeFilter

from course_tree.pagination import CourseTreeNodePagination
from .serializers import CourseTreeNodePolymorphicSerializer
from .models import BaseCourseTreeNode, RootCourseTreeNode
from django.http import FileResponse, Http404
from . import policies
from django.db.models import OuterRef, Subquery
from mptt.exceptions import InvalidMove
from django_filters.rest_framework import DjangoFilterBackend


class TreeNodeViewSet(viewsets.ModelViewSet):
    serializer_class = CourseTreeNodePolymorphicSerializer
    queryset = BaseCourseTreeNode.objects.all()
    permission_classes = [policies.TreeNodePolicy]
    pagination_class = CourseTreeNodePagination
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = CourseTreeNodeFilter

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
        )

    def get_queryset(self):
        qs = super().get_queryset()

        # this is always true with the current route definition
        if self.kwargs.get("course_pk") is not None:
            # filter to only get nodes in a tree whose root references the requested course
            node_root_subquery = (
                BaseCourseTreeNode.objects.all().filter(  # get root nodes
                    tree_id=OuterRef("tree_id"), parent_id__isnull=True
                )
            )
            nodes_with_course_qs = BaseCourseTreeNode.objects.annotate(
                root_course_id=Subquery(  # annotate nodes with the course_id attribute of the root node of their tree
                    # ! assumes that there is at most one tree per course - currently enforced
                    node_root_subquery.values("rootcoursetreenode__course_id")[:1]
                )
            )
            try:
                qs = nodes_with_course_qs.filter(
                    root_course_id=self.kwargs["course_pk"]
                )
            except ValueError:  # invalid value for course_pk
                raise Http404

        if self.request.query_params.get("top_level", "").lower() in ["true", "1"]:
            # request is for nodes that are direct child of the root node for the tree
            qs = qs.filter(level=1)
        elif self.kwargs.get("parent_pk") is not None:
            # using the viewset as a sub-route to get the children of a node
            try:
                qs = qs.filter(parent_id=self.kwargs["parent_pk"])
            except ValueError:  # invalid value for parent_pk
                raise Http404

        return qs.order_by("-created")  # TODO temporary, remove

    @action(detail=False, methods=["get"])
    def root_id(self, request, **kwargs):
        try:
            # TODO this assumes there's only one tree per course, keep an eye on it
            root, _ = RootCourseTreeNode.objects.get_or_create(
                course_id=self.kwargs["course_pk"]
            )
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(root.id)

    @action(detail=True, methods=["post"])
    def move(self, request, **kwargs):
        params = request.query_params
        node = self.get_object()

        target_id = params.get("target")
        position = params.get("position")

        if target_id is None or position is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        target = get_object_or_404(BaseCourseTreeNode, pk=target_id)

        try:
            node.move_to(target=target, position=position)
        except InvalidMove:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def download(self, request, **kwargs):
        file = self.get_object().file

        if not bool(file):
            return Response(status=status.HTTP_204_NO_CONTENT)

        return FileResponse(
            file,
            as_attachment=True,
            filename=os.path.split(file.name)[1],
        )

    @action(detail=True, methods=["get"])
    def thumbnail(self, request, **kwargs):
        file = self.get_object().thumbnail

        if not bool(file):
            return Response(status=status.HTTP_204_NO_CONTENT)

        return FileResponse(
            file,
            as_attachment=True,
            filename=os.path.split(file.name)[1],
        )
