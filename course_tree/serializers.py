from rest_framework import serializers

from course_tree.pagination import CourseTreeChildrenNodePagination
from users.serializers import UserSerializer

from .models import (
    AnnouncementNode,
    NodeComment,
    RootCourseTreeNode,
    TopicNode,
    LessonNode,
    FileNode,
)
from courses.serializer_fields import RecursiveField, FileWithPreviewField
from rest_polymorphic.serializers import PolymorphicSerializer

from rest_framework import serializers


class CourseTreeNodeSerializer(serializers.ModelSerializer):
    include_children = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.include_children:
            # self.fields["children"] = serializers.ListSerializer(
            #     read_only=True,
            #     child=RecursiveField(to="CourseTreeNodePolymorphicSerializer"),
            # )
            self.fields["children"] = serializers.SerializerMethodField(
                "get_paginated_children"
            )

        self.fields["parent_id"] = serializers.IntegerField()

        # ! TODO remove after debug
        self.fields["lft"] = serializers.IntegerField(read_only=True)
        self.fields["tree_id"] = serializers.IntegerField(read_only=True)

    def get_paginated_children(self, obj):
        paginator = CourseTreeChildrenNodePagination()
        request = self.context.get("request")
        children = paginator.paginate_queryset(
            obj.children.all(),
            request,
        )

        serializer = CourseTreeNodePolymorphicSerializer(
            children,
            read_only=True,
            many=True,
            context=self.context,
        )
        return paginator.get_paginated_response(serializer.data).data


class RootNodeSerializer(CourseTreeNodeSerializer):
    class Meta:
        model = RootCourseTreeNode
        fields = ["id"]


class TopicNodeSerializer(CourseTreeNodeSerializer):
    class Meta:
        model = TopicNode
        fields = ["id", "name"]


class LessonNodeSerializer(CourseTreeNodeSerializer):
    creator = UserSerializer(read_only=True)

    class Meta:
        model = LessonNode
        fields = [
            "id",
            "title",
            "creator",
            "body",
            "state",
        ]


class AnnouncementNodeSerializer(CourseTreeNodeSerializer):
    creator = UserSerializer(read_only=True)

    class Meta:
        model = AnnouncementNode
        fields = [
            "id",
            "creator",
            "body",
            "state",
        ]


class FileNodeSerializer(CourseTreeNodeSerializer):
    file = FileWithPreviewField(allow_null=True)
    creator = UserSerializer(read_only=True)

    class Meta:
        model = FileNode
        fields = [
            "id",
            "creator",
            "file",
            "mime_type",
            "thumbnail",
        ]

    def create(self, validated_data):
        # getting the path to a FileNode's file requires knowing its primary key.
        # therefore, if the creation payload contains a file, the node is created
        # first without the file, and the file is subsequently assigned to it
        file = validated_data.pop("file", None)
        instance = super().create(validated_data)
        if file is not None:
            instance.file = file
            instance.save()
        return instance


class CourseTreeNodePolymorphicSerializer(PolymorphicSerializer):
    # TODO write docs
    model_serializer_mapping = {
        RootCourseTreeNode: RootNodeSerializer,
        TopicNode: TopicNodeSerializer,
        LessonNode: LessonNodeSerializer,
        FileNode: FileNodeSerializer,
        AnnouncementNode: AnnouncementNodeSerializer,
    }


class NodeCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_edited = serializers.SerializerMethodField()

    class Meta:
        model = NodeComment
        fields = ["id", "user", "created", "is_edited", "comment"]

    def get_is_edited(self, obj):
        return obj.created != obj.modified
