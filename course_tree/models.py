import io
from django.db import models
from django.db.models import Q
import os
from polymorphic_tree.models import PolymorphicMPTTModel, PolymorphicTreeForeignKey
from mptt.models import MPTTOptions
from course_tree.helpers import detect_content_type, get_file_thumbnail
from course_tree.managers import CourseTreeNodeManager
from courses.models import Course, TimestampableModel
from users.models import User
from django.core.files.images import ImageFile
from polymorphic_tree.models import _get_base_polymorphic_model


import logging

logger = logging.getLogger(__name__)


def get_filenode_file_path(node: "FileNode", filename: str):
    root: RootCourseTreeNode = node.get_root()
    course = root.course
    return f"course_tree/{str(course.pk)}/file_nodes/{str(node.pk)}/{filename}"


# monkey patch MPTTOptions to fix https://github.com/django-polymorphic/django-polymorphic-tree/issues/87
def get_ordered_insertion_target(self, node, parent):
    """
    Attempts to retrieve a suitable right sibling for ``node``
    underneath ``parent`` (which may be ``None`` in the case of root
    nodes) so that ordering by the fields specified by the node's class'
    ``order_insertion_by`` option is maintained.

    Returns ``None`` if no suitable sibling can be found.
    """
    right_sibling = None
    # Optimisation - if the parent doesn't have descendants,
    # the node will always be its last child.
    if self.order_insertion_by and (
        parent is None or parent.get_descendant_count() > 0
    ):
        opts = node._mptt_meta
        order_by = opts.order_insertion_by[:]
        filters = self.insertion_target_filters(node, order_by)
        if parent:
            filters = filters & Q(**{opts.parent_attr: parent})
            # Fall back on tree ordering if multiple child nodes have
            # the same values.
            order_by.append(opts.left_attr)
        else:
            filters = filters & Q(**{opts.parent_attr: None})
            # Fall back on tree id ordering if multiple root nodes have
            # the same values.
            order_by.append(opts.tree_id_attr)
        queryset = (
            # the original code does `node.__class__`, here we need to get
            # the base polymorphic model instead, so insertion order can
            # query all nodes that inherit from our base node model
            _get_base_polymorphic_model(node.__class__)
            ._tree_manager.db_manager(node._state.db)
            .filter(filters)
            .order_by(*order_by)
        )
        if node.pk:
            queryset = queryset.exclude(pk=node.pk)
        try:
            right_sibling = queryset[:1][0]
        except IndexError:
            # No suitable right sibling could be found
            pass
    return right_sibling


MPTTOptions.get_ordered_insertion_target = get_ordered_insertion_target


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

    objects = CourseTreeNodeManager()

    class MPTTMeta:
        order_insertion_by = ["lft"]

    # def __new__(cls: type[Self]) -> Self:
    #     return super().__new__()

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
        return "Root " + str(self.pk)

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


class AnnouncementNode(BaseCourseTreeNode):
    class AnnouncementState(models.IntegerChoices):
        DRAFT = 0
        PUBLISHED = 1
        # SCHEDULED = 2

    body = models.TextField(blank=True)
    state = models.PositiveSmallIntegerField(
        default=AnnouncementState.DRAFT, choices=AnnouncementState.choices
    )


class PollNode(BaseCourseTreeNode):
    class PollState(models.IntegerChoices):
        DRAFT = 0
        OPEN = 1
        CLOSED = 2

    text = models.TextField(blank=True)
    state = models.PositiveSmallIntegerField(
        default=PollState.DRAFT, choices=PollState.choices
    )

    def can_vote(self, user: User):
        return (
            self.state == self.PollState.OPEN
            and not self.participations.filter(user=user).exists()
        )


class PollNodeChoice(models.Model):
    poll = models.ForeignKey(
        PollNode,
        related_name="choices",
        on_delete=models.CASCADE,
    )
    text = models.CharField(max_length=500)

    def get_selection_count(self):
        return self.poll.participations.filter(selected_choice=self).count()

    def is_selected_by(self, user):
        try:
            participation = self.poll.participations.get(user=user)
        except PollNodeParticipation.DoesNotExist:
            return False
        return participation.selected_choice == self


class PollNodeParticipation(TimestampableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(
        PollNode,
        related_name="participations",
        on_delete=models.CASCADE,
    )
    selected_choice = models.ForeignKey(PollNodeChoice, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["poll_id", "user_id"],
                name="poll_participation_unique_user",
            )
        ]


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

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, value):
        self._file = value

        try:
            # intercept file updates to update mime type
            self.mime_type = detect_content_type(value)
        except Exception as e:
            # TODO handle exception
            logger.critical(
                "Error while detecting mime type for file "
                + str(self.file.name)
                + " for node with id "
                + str(self.pk)
                + ": "
                + str(e)
            )

        try:
            # update thumbnail for new file
            thumbnail = get_file_thumbnail(self.file, self.mime_type)
            if thumbnail is not None:
                self.thumbnail = ImageFile(io.BytesIO(thumbnail), name="thumbnail.jpg")
        except Exception as e:
            # TODO handle exception
            logger.critical(
                "Error while updating thumbnail for file "
                + str(self.file.name)
                + " for node with id "
                + str(self.pk)
                + ": "
                + str(e)
            )

    def check_file_exists(self):
        """
        Sanity check to verify that the file associated to this
        FileNode exists in the storage
        """
        res = self.file.storage.exists(self.file.name)
        if not res:
            logger.critical(
                "File associated with node "
                + str(self.pk)
                + " with name "
                + str(self.file.name)
                + " doesn't exist"
            )
        return res


class NodeComment(TimestampableModel):
    user = models.ForeignKey(
        User,
        related_name="comments",
        on_delete=models.SET_NULL,
        null=True,
    )
    node = models.ForeignKey(
        BaseCourseTreeNode,
        related_name="comments",
        on_delete=models.CASCADE,
    )
    comment = models.CharField(max_length=500)

    class Meta:
        ordering = (
            "node_id",
            "created",
        )
