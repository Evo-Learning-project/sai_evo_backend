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


class EventTemplate(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="event_templates",
    )
    name = models.TextField(blank=True)
    public = models.BooleanField()
    creator = models.ForeignKey("users.User")


class EventTemplateRule(models.Model):
    RANDOM = 0
    SPECIFIC = 1

    RULE_TYPES = (
        (RANDOM, "Rule to pick random exercises"),
        (SPECIFIC, "Rule to include a specific exercise"),
    )

    template = models.ForeignKey(
        EventTemplate,
        on_delete=models.CASCADE,
        related_name="rules",
    )
    rule_type = models.PositiveSmallIntegerField(choices=RULE_TYPES)
    exercise = models.ForeignKey(
        "courses.Exercise",
        null=True,
        blank=True,
    )
    amount = models.PositiveIntegerField(null=True, blank=True)


class EventTemplateRuleClause(models.Model):
    rule = models.ForeignKey(EventTemplateRule, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
