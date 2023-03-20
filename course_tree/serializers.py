from rest_framework import serializers
from django.db.models import Sum, Case, When, Value
from courses.logic.privileges import MANAGE_COURSE_TREE_NODES, check_privilege
from integrations.serializers import IntegrationModelSerializer

# from course_tree.pagination import CourseTreeChildrenNodePagination
from users.serializers import UserSerializer

from .models import (
    AnnouncementNode,
    NodeComment,
    PollNode,
    PollNodeChoice,
    RootCourseTreeNode,
    TopicNode,
    LessonNode,
    FileNode,
)
from courses.serializer_fields import RecursiveField, FileWithPreviewField
from rest_polymorphic.serializers import PolymorphicSerializer

from rest_framework import serializers


class CourseTreeNodeSerializer(serializers.ModelSerializer):
    # include_children = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["parent_id"] = serializers.IntegerField()

        # ! TODO remove after debug
        self.fields["lft"] = serializers.IntegerField(read_only=True)
        self.fields["tree_id"] = serializers.IntegerField(read_only=True)


class RootNodeSerializer(CourseTreeNodeSerializer):
    class Meta:
        model = RootCourseTreeNode
        fields = ["id"]


class TopicNodeSerializer(CourseTreeNodeSerializer):
    class Meta:
        model = TopicNode
        fields = ["id", "name"]


class LessonNodeSerializer(IntegrationModelSerializer, CourseTreeNodeSerializer):
    creator = UserSerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = LessonNode
        fields = [
            "id",
            "title",
            "creator",
            "body",
            "state",
            "comment_count",
            "created",
            "modified",
        ]

    def get_comment_count(self, obj):
        return obj.comments.count()


class AnnouncementNodeSerializer(IntegrationModelSerializer, CourseTreeNodeSerializer):
    creator = UserSerializer(read_only=True)

    class Meta:
        model = AnnouncementNode
        fields = [
            "id",
            "creator",
            "body",
            "state",
            "created",
            "modified",
        ]


class PollNodeChoiceSerializer(serializers.ModelSerializer):
    selected = serializers.SerializerMethodField()

    class Meta:
        model = PollNodeChoice
        fields = ["id", "text", "selected"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.get("hide_selection_count", False):
            self.fields["votes"] = serializers.SerializerMethodField()

    def get_votes(self, obj):
        # return obj.choices.aggregate(votes=Sum("selections__count", default=0))["votes"]
        return obj.get_selection_count()

    def get_selected(self, obj):
        user = self.context["request"].user
        return obj.is_selected_by(user)  # user in obj.selections.all()


class PollNodeSerializer(CourseTreeNodeSerializer):
    choices = serializers.SerializerMethodField()  # to pass context
    creator = UserSerializer(read_only=True)

    class Meta:
        model = PollNode
        fields = [
            "id",
            "text",
            "state",
            "choices",
            "creator",
            "created",
            "modified",
        ]

    def get_choices(self, obj):
        user = self.context.get("request").user
        hide_selection_count = obj.can_vote(user) and not check_privilege(
            user, obj.get_course(), MANAGE_COURSE_TREE_NODES
        )
        return PollNodeChoiceSerializer(
            obj.choices.all(),
            many=True,
            read_only=True,
            context={"hide_selection_count": hide_selection_count, **self.context},
        ).data


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
            "created",
            "modified",
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
        PollNode: PollNodeSerializer,
    }


class NodeCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_edited = serializers.SerializerMethodField()

    class Meta:
        model = NodeComment
        fields = ["id", "user", "created", "is_edited", "comment"]

    def get_is_edited(self, obj):
        return obj.created != obj.modified
