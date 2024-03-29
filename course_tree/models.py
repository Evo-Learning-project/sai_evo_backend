import io
import json
import logging
import os

from django_celery_beat.models import PeriodicTask, ClockedSchedule

from courses.models import Course, TimestampableModel
from django.core.files.images import ImageFile
from django.db import models
from django.db.models import Q
from mptt.models import MPTTOptions
from polymorphic_tree.models import (
    PolymorphicMPTTModel,
    PolymorphicTreeForeignKey,
    _get_base_polymorphic_model,
)
from integrations.mixins import IntegrationModelMixin
from integrations.registry import IntegrationRegistry
from users.models import User

from course_tree.helpers import detect_content_type, get_file_thumbnail
from course_tree.managers import CourseTreeNodeManager

from django.conf import settings

from .tasks import publish_scheduled_node

from django.utils import timezone


from django_lifecycle import (
    LifecycleModel,
    LifecycleModelMixin,
    hook,
    BEFORE_UPDATE,
    AFTER_UPDATE,
    AFTER_CREATE,
    BEFORE_DELETE,
)


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

    def get_absolute_url(self):
        return f"{settings.BASE_FRONTEND_URL}/courses/{self.get_course().pk}/material/{self.pk}/"

    def get_course(self) -> Course:
        return self.get_root().course


class SchedulableModel(LifecycleModelMixin, models.Model):
    schedule_publish_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_draft(self):
        raise NotImplementedError

    def publish(self):
        raise NotImplementedError

    @hook(AFTER_CREATE, when="schedule_publish_at", is_not=None)
    @hook(AFTER_UPDATE, when="schedule_publish_at", has_changed=True, is_not=None)
    def on_schedule(self):
        if self.is_draft:
            # create a clocked schedule for the value of `schedule_publish_at`
            schedule, _ = ClockedSchedule.objects.get_or_create(
                clocked_time=self.schedule_publish_at,
            )
            # schedule the task to publish the node
            task_name = publish_scheduled_node.name
            PeriodicTask.objects.create(
                name=(
                    f"{task_name}_{self.pk}_{self.schedule_publish_at.isoformat()}"
                    f"_{timezone.localtime(timezone.now()).isoformat()}"
                ),
                clocked=schedule,
                one_off=True,
                task=task_name,
                args=json.dumps([self._meta.model_name, self.pk]),
            )


class RootCourseTreeNode(BaseCourseTreeNode):
    course = models.ForeignKey(
        Course,
        related_name="trees",
        on_delete=models.PROTECT,
    )

    can_be_root = True


class TopicNode(BaseCourseTreeNode):
    name = models.CharField(max_length=200, blank=True)


class LessonNode(
    SchedulableModel,
    LifecycleModelMixin,
    BaseCourseTreeNode,
    IntegrationModelMixin,
):
    class LessonState(models.IntegerChoices):
        DRAFT = 0
        PUBLISHED = 1

    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    state = models.PositiveSmallIntegerField(
        default=LessonState.DRAFT, choices=LessonState.choices
    )

    @property
    def is_draft(self):
        return self.state == self.LessonState.DRAFT

    def publish(self):
        self.state = self.LessonState.PUBLISHED
        self.save()

    @hook(
        AFTER_UPDATE,
        when="state",
        changes_to=LessonState.PUBLISHED,
        was=LessonState.DRAFT,
    )
    def on_publish(self):
        fire_integration_event = getattr(self, "_fire_integration_event", False)
        if fire_integration_event:
            IntegrationRegistry().dispatch(
                "lesson_published",
                course=self.get_course(),
                user=self.creator,
                lesson=self,
            )


class AnnouncementNode(
    SchedulableModel,
    LifecycleModelMixin,
    BaseCourseTreeNode,
    IntegrationModelMixin,
):
    class AnnouncementState(models.IntegerChoices):
        DRAFT = 0
        PUBLISHED = 1

    body = models.TextField(blank=True)
    state = models.PositiveSmallIntegerField(
        default=AnnouncementState.DRAFT, choices=AnnouncementState.choices
    )

    @property
    def is_draft(self):
        return self.state == self.AnnouncementState.DRAFT

    def publish(self):
        self.state = self.AnnouncementState.PUBLISHED
        self.save()

    @hook(
        AFTER_UPDATE,
        when="state",
        changes_to=AnnouncementState.PUBLISHED,
        was=AnnouncementState.DRAFT,
    )
    def on_publish(self):
        fire_integration_event = getattr(self, "_fire_integration_event", False)
        if fire_integration_event:
            IntegrationRegistry().dispatch(
                "announcement_published",
                course=self.get_course(),
                user=self.creator,
                announcement=self,
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
        # TODO optimize with prefetching once https://github.com/django-polymorphic/django-polymorphic/pull/531 is solved
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
    # TODO use reverse relation on this field in get_selection_count
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
        res = bool(self.file) and self.file.storage.exists(self.file.name)
        if not res:
            logger.critical(
                "File associated with node "
                + str(self.pk)
                + " with name "
                + str(self.file.name)
                + " doesn't exist"
            )
        return res

    def check_thumbnail_exists(self):
        """
        Sanity check to verify that the thumbnail associated to this
        FileNode exists in the storage
        """
        res = bool(self.thumbnail) and self.file.storage.exists(self.thumbnail.name)
        # if not res:
        #     logger.warning(
        #         "Thumbnail associated with node " + str(self.pk) + " doesn't exist"
        #     )
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
