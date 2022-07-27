from django.db import models
from core.models import HashIdModel

from courses.abstract_models import TimestampableModel
from users.models import User


# class DiscussionThread(TimestampableModel):
#     DRAFT = 0
#     OPEN = 1
#     LOCKED = 2

#     STATES = (
#         (DRAFT, "Draft"),
#         (OPEN, "Open"),
#         (LOCKED, "Locked"),
#     )

#     opening_post = models.OneToOneField("Post")
#     user = models.ForeignKey(User, related_name="threads")
#     course = models.ForeignKey(Course, related_name="threads")
#     state = models.PositiveSmallIntegerField(choices=STATES, default=DRAFT)


# class Post(TimestampableModel, OrderableModel):
#     ORDER_WITH_RESPECT_TO_FIELD = "thread"

#     user = models.ForeignKey(User, related_name="posts")
#     thread = models.ForeignKey(DiscussionThread, related_name="posts")
#     content = models.ForeignKey("Content")


class Content(HashIdModel, TimestampableModel):
    """
    Represents a generic piece of content that is to be associated
    to other models for processing & displaying
    """

    def get_attachment_path(self, obj, filename):
        return f"attachments/{obj.id}/{filename}"

    text_content = models.TextField(blank=True)
    file_content = models.FileField(
        null=True,
        blank=True,
        upload_to=get_attachment_path,
    )

    def __str__(self):
        return self.text_content[:100]


class PostModel(TimestampableModel):
    """
    An abstract model representing a post or comment that a user
    has made regarding a (model containing a) piece of content
    """

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.ForeignKey(Content, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class VoteModel(TimestampableModel):
    """
    An abstract model representing a vote that a user ha
    cast for a (model containing a) piece of content
    """

    UP_VOTE = 0
    DOWN_VOTE = 1

    VOTE_TYPES = (
        (UP_VOTE, "Up vote"),
        (DOWN_VOTE, "Down vote"),
    )

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    vote_type = models.PositiveSmallIntegerField(choices=VOTE_TYPES)

    class Meta:
        abstract = True
