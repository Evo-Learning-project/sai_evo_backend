import io
from django.db import models
import os
from polymorphic_tree.models import PolymorphicMPTTModel, PolymorphicTreeForeignKey
from course_tree.helpers import detect_content_type, get_file_thumbnail
from courses.models import Course, TimestampableModel
from users.models import User
from django.core.files.images import ImageFile


def get_filenode_file_path(node: "FileNode", filename: str):
    root: RootCourseTreeNode = node.get_root()
    course = root.course
    return f"course_tree/{str(course.pk)}/file_nodes/{str(node.pk)}/{filename}"


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

    class MPTTMeta:
        order_insertion_by = [
            "-created"
        ]  # TODO need something more sophisticated in order to handle reodering

    # class Meta(PolymorphicMPTTModel.Meta):
    #     verbose_name = _("Tree node")
    #     verbose_name_plural = _("Tree nodes")

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

    _file = models.FileField(
        db_column="file", blank=True, null=True, upload_to=get_filenode_file_path
    )
    mime_type = models.CharField(max_length=255, blank=True)
    thumbnail = models.ImageField(
        blank=True,
        null=True,
        upload_to=get_filenode_file_path,
    )

    def save(self, generate_thumbnail=True, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file is not None and generate_thumbnail:
            thumbnail = get_file_thumbnail(self.file, self.mime_type)
            if thumbnail is not None:
                self.thumbnail = ImageFile(io.BytesIO(thumbnail), name="thumbnail.jpg")
                self.save(update_fields=["thumbnail"], generate_thumbnail=False)

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, value):
        # intercept file updates to update mime type
        self._file = value
        self.mime_type = detect_content_type(value)
        # self.thumbnail = get_file_thumbnail(value, self.mime_type)

    @property
    def file_type(self):
        # TODO use python_magic to return the actual type
        return os.path.splitext(self.file.name)[1]
