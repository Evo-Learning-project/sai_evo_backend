from django.db.models import Exists, OuterRef
from rest_framework import serializers

from .models import (
    RootCourseTreeNode,
    TopicNode,
    LessonNode,
    FileNode,
    BaseCourseTreeNode,
)
from courses.serializer_fields import RecursiveField, FileWithPreviewField
from rest_polymorphic.serializers import PolymorphicSerializer
import importlib
import inspect
import os

from rest_framework.fields import Field
from rest_framework.serializers import BaseSerializer, SerializerMethodField
from rest_framework import serializers


class CourseTreeNodeSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["children"] = serializers.ListSerializer(
            read_only=True,
            child=RecursiveField(to="CourseTreeNodePolymorphicSerializer"),
        )

        self.fields["parent_id"] = serializers.IntegerField()


class RootNodeSerializer(CourseTreeNodeSerializer):
    class Meta:
        model = RootCourseTreeNode
        fields = ["id"]


class TopicNodeSerializer(CourseTreeNodeSerializer):
    class Meta:
        model = TopicNode
        fields = ["id", "name"]


class LessonNodeSerializer(CourseTreeNodeSerializer):
    class Meta:
        model = LessonNode
        fields = [
            "id",
            "title",
            "body",
        ]


class FileNodeSerializer(CourseTreeNodeSerializer):
    file = FileWithPreviewField()

    class Meta:
        model = FileNode
        fields = [
            "id",
            "file",
        ]


class CourseTreeNodePolymorphicSerializer(PolymorphicSerializer):
    # TODO write docs
    model_serializer_mapping = {
        RootCourseTreeNode: RootNodeSerializer,
        TopicNode: TopicNodeSerializer,
        LessonNode: LessonNodeSerializer,
        FileNode: FileNodeSerializer,
    }
