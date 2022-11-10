from django.db import models

from polymorphic_tree.models import PolymorphicMPTTModel, PolymorphicTreeForeignKey
from courses.models import Course, TimestampableModel
from users.models import User


class BaseCourseTreeNode(PolymorphicMPTTModel, TimestampableModel):
    # TODO write docs for all nodes
    parent = PolymorphicTreeForeignKey(
        "self",
        blank=True,
        null=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    creator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    can_be_root = False
    can_have_children = True

    @property
    def displayed_name(self):
        """For admin"""
        child_display_attrs = ("topicnode", "rootnode", "lessonnode", "filenode")
        for at in child_display_attrs:
            try:
                hasattr(self, at)
                return getattr(self, at)
            except:
                pass
        return "Root"

    def get_course(self) -> Course:
        return self.get_root().course

    # class Meta(PolymorphicMPTTModel.Meta):
    #     verbose_name = _("Tree node")
    #     verbose_name_plural = _("Tree nodes")


class RootCourseTreeNode(BaseCourseTreeNode):
    course = models.ForeignKey(
        Course,
        related_name="trees",
        on_delete=models.PROTECT,
    )

    can_be_root = True


class TopicNode(BaseCourseTreeNode):
    name = models.CharField(max_length=200, blank=True)


class LessonNode(BaseCourseTreeNode):
    class LessonState(models.IntegerChoices):
        DRAFT = 0
        PUBLISHED = 1
        # SCHEDULED = 2

    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    state = models.PositiveSmallIntegerField(
        default=LessonState.DRAFT, choices=LessonState.choices
    )


class FileNode(BaseCourseTreeNode):
    can_have_children = False

    def get_file_path(self, node: "FileNode", filename: str):
        root: RootCourseTreeNode = node.get_root()
        course = root.course
        return f"course_tree/{str(course.pk)}/file_nodes/{str(self.pk)}/{filename}"

    file = models.FileField(blank=True, null=True, upload_to=get_file_path)
