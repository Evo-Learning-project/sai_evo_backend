from django.db import models
from django.db.models import Q
from .models import LessonNode, AnnouncementNode, PollNode, FileNode, TopicNode
from polymorphic.query import PolymorphicQuerySet


class CourseTreeNodeQuerySet(PolymorphicQuerySet):
    def restrict_to_public_states(self):
        """
        Filters the queryset so it only contains nodes whose current state
        allows them to be seen by unprivileged users.

        The field and values vary depending on the inheriting node, so
        this filter is polymorphic.
        """
        return self.filter(
            Q(LessonNode___state=LessonNode.LessonState.PUBLISHED)
            | Q(AnnouncementNode___state=AnnouncementNode.AnnouncementState.PUBLISHED)
            | Q(
                PollNode___state__in=[
                    PollNode.PollState.OPEN,
                    PollNode.PollState.CLOSED,
                ]
            )
            # file & topic nodes don't have a state that can make them private
            | Q(instance_of=FileNode)
            | Q(instance_of=TopicNode)
        )
