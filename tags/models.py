from django.db import models


class Tag(models.Model):
    DIFFICULTY_TAG = 0
    TOPIC_TAG = 1
    EVENT_SPECIFIC_TAG = 2
    GENERIC_TAG = 3

    TAG_TYPES = (
        (DIFFICULTY_TAG, "Difficulty"),
        (TOPIC_TAG, "Topic"),
        (EVENT_SPECIFIC_TAG, "Event-specific"),
        (GENERIC_TAG, "Generic"),
    )

    course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        related_name="tags",
        on_delete=models.CASCADE,
    )
    event = models.ForeignKey(
        "courses.Event",
        null=True,
        blank=True,
        related_name="tags",
        on_delete=models.CASCADE,
    )
    name = models.TextField()
    tag_type = models.PositiveSmallIntegerField(choices=TAG_TYPES)
