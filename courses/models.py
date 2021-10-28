from django.db import models
from users.models import User

from .logic.grading import apply_grading_rule
from .managers import (
    EventInstanceManager,
    EventParticipationManager,
    ExerciseManager,
    ParticipationAssessmentManager,
    ParticipationSubmissionManager,
)


class SlotNumberedModel(models.Model):
    slot_number = models.PositiveIntegerField()

    class Meta:
        abstract = True


class Course(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_courses",
        null=True,
    )
    teachers = models.ManyToManyField("users.User", blank=True)
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Exercise(models.Model):
    MULTIPLE_CHOICE_SINGLE_POSSIBLE = 0
    MULTIPLE_CHOICE_MULTIPLE_POSSIBLE = 1
    OPEN_ANSWER = 2
    COMPLETION = 3
    AGGREGATED = 4
    JS = 5
    ATTACHMENT = 6

    EXERCISE_TYPES = (
        (MULTIPLE_CHOICE_SINGLE_POSSIBLE, "Multiple choice, single possible"),
        (MULTIPLE_CHOICE_MULTIPLE_POSSIBLE, "Multiple choice, multiple possible"),
        (OPEN_ANSWER, "Open answer"),
        (COMPLETION, "Completion"),
        (AGGREGATED, "Aggregated"),
        (JS, "JavaScript"),
        (ATTACHMENT, "Attachment"),
    )

    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="exercises"
    )
    parent = models.ForeignKey(
        "Exercise",
        null=True,
        blank=True,
        related_name="sub_exercises",
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField("tags.Tag", blank=True)
    exercise_type = models.PositiveSmallIntegerField(choices=EXERCISE_TYPES)
    text = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    draft = models.BooleanField(default=False)

    objects = ExerciseManager()

    def __str__(self):
        return self.text[:100]

    def clean(self):
        # TODO enforce constraints on the various types of question
        pass


class ExerciseChoice(models.Model):
    exercise = models.ForeignKey(
        Exercise, related_name="choices", on_delete=models.CASCADE
    )
    text = models.TextField()
    correct = models.BooleanField()

    def __str__(self):
        return str(self.exercise) + " - " + self.text[:100]


class ExerciseTestCase(models.Model):
    exercise = models.ForeignKey(
        Exercise, related_name="testcases", on_delete=models.CASCADE
    )
    code = models.TextField()
    label = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return str(self.exercise) + " - " + self.code


class Event(models.Model):
    SELF_SERVICE_PRACTICE = 0
    IN_CLASS_PRACTICE = 1
    EXAM = 2
    ASSIGNMENT = 3
    EXTERNAL = 4

    EVENT_TYPES = (
        (SELF_SERVICE_PRACTICE, "Self-service practice"),
        (IN_CLASS_PRACTICE, "In-class practice"),
        (EXAM, "Exam"),
        (ASSIGNMENT, "Assignment"),
        (EXTERNAL, "External resource"),
    )

    ALL_EXERCISES_AT_ONCE = 0
    ONE_AT_A_TIME_CAN_GO_BACK = 1
    ONE_AT_A_TIME_CANNOT_GO_BACK = 2

    PROGRESSION_RULES = (
        (ALL_EXERCISES_AT_ONCE, "All exercises at once"),
        (ONE_AT_A_TIME_CAN_GO_BACK, "One at a time, can go back"),
        (ONE_AT_A_TIME_CANNOT_GO_BACK, "One at a time, cannot go back"),
    )

    DRAFT = 0
    PLANNED = 1
    OPEN = 2
    CLOSED = 3

    EVENT_STATES = (
        (DRAFT, "Draft"),
        (PLANNED, "Planned"),
        (OPEN, "Open"),
        (CLOSED, "Closed"),
    )

    name = models.TextField()
    instructions = models.TextField(blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="events",
    )
    begin_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField()
    event_type = models.PositiveIntegerField(choices=EVENT_TYPES)
    progression_rule = models.PositiveIntegerField(choices=PROGRESSION_RULES)
    state = models.PositiveIntegerField(choices=EVENT_STATES)
    template = models.ForeignKey(
        "EventTemplate",
        related_name="events",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.name

    # TODO unique [course, name]


class EventTemplate(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="event_templates",
    )
    name = models.TextField(blank=True)
    public = models.BooleanField()
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
    )


class EventTemplateRule(SlotNumberedModel):
    TAG_BASED = 0
    ID_BASED = 1

    RULE_TYPES = (
        (TAG_BASED, "Tag-based rule"),
        (ID_BASED, "Exercise ID-based rule"),
    )

    template = models.ForeignKey(
        EventTemplate,
        on_delete=models.CASCADE,
        related_name="rules",
    )
    rule_type = models.PositiveSmallIntegerField(choices=RULE_TYPES)
    exercises = models.ManyToManyField(
        "courses.Exercise",
        blank=True,
    )


class EventTemplateRuleClause(models.Model):
    rule = models.ForeignKey(EventTemplateRule, on_delete=models.CASCADE)
    tags = models.ManyToManyField("tags.Tag")


class EventInstance(models.Model):
    """
    Represents a concrete instance of an event. The event template is applied to get a
    concrete list of exercises assigned to the instance applying the template rules
    """

    event = models.ForeignKey(
        Event,
        related_name="instances",
        on_delete=models.PROTECT,
    )
    exercises = models.ManyToManyField(
        Exercise,
        through="EventInstanceSlot",
        blank=True,
    )

    objects = EventInstanceManager()


class EventInstanceSlot(SlotNumberedModel):
    event_instance = models.ForeignKey(
        EventInstance,
        related_name="slots",
        on_delete=models.CASCADE,
    )
    exercise = models.ForeignKey(
        Exercise,
        related_name="slots",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["event_instance_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["event_instance_id", "slot_number"],
                name="event_instance_unique_slot_number",
            )
        ]


class ParticipationAssessment(models.Model):
    """
    Represents the assessment (score, comments) of the participation to an event, either
    issued by a teacher or compiled automatically
    """

    NOT_GRADED = 0
    PARTIALLY_GRADED = 1
    FULLY_GRADED = 2

    GRADING_STATES = (
        (NOT_GRADED, "Not graded"),
        (PARTIALLY_GRADED, "Partially graded"),
        (FULLY_GRADED, "Fully graded"),
    )

    state = models.PositiveSmallIntegerField(choices=GRADING_STATES, default=NOT_GRADED)

    objects = ParticipationAssessmentManager()


class ParticipationAssessmentSlot(SlotNumberedModel):
    NOT_GRADED = 0
    GRADED = 1

    GRADING_STATES = (
        (NOT_GRADED, "Not graded"),
        (GRADED, "Graded"),
    )
    assessment = models.ForeignKey(
        ParticipationAssessment,
        related_name="slots",
        on_delete=models.CASCADE,
    )
    comment = models.TextField(blank=True)
    _score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["assessment_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment_id", "slot_number"],
                name="assessment_unique_slot_number",
            )
        ]

    @property
    def score(self):
        if self._score is None:
            # TODO apply rule
            pass
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def state(self):
        return self.GRADED if self.score is not None else self.NOT_GRADED


class ParticipationSubmission(models.Model):
    objects = ParticipationSubmissionManager()


class ParticipationSubmissionSlot(SlotNumberedModel):
    submission = models.ForeignKey(
        ParticipationSubmission,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    seen_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    selected_choice = models.ForeignKey(
        ExerciseChoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    answer_text = models.TextField(blank=True)

    class Meta:
        ordering = ["submission_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission_id", "slot_number"],
                name="participation_submission_unique_slot_number",
            )
        ]


class EventParticipation(models.Model):
    IN_PROGRESS = 0
    TURNED_IN = 1

    PARTICIPATION_STATES = (
        (IN_PROGRESS, "In progress"),
        (TURNED_IN, "Turned in"),
    )

    event_instance = models.ForeignKey(
        EventInstance,
        related_name="participations",
        on_delete=models.PROTECT,
    )
    assessment = models.OneToOneField(
        ParticipationAssessment,
        on_delete=models.CASCADE,
        related_name="participation",
        null=True,
    )
    submission = models.OneToOneField(
        ParticipationSubmission,
        on_delete=models.CASCADE,
        related_name="participation",
        null=True,
    )
    user = models.ForeignKey(
        User,
        related_name="events",
        on_delete=models.PROTECT,
    )
    begin_timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True, blank=True)
    state = models.PositiveSmallIntegerField(choices=PARTICIPATION_STATES)
    current_slot_number = models.PositiveIntegerField(null=True, blank=True)

    objects = EventParticipationManager()

    def __str__(self):
        return str(self.event) + " - " + str(self.user)

    @property
    def current_exercise(self):
        return self.assigned_exercises.get(position=self.current_exercise_cursor)


class ExerciseGradingRule(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="exercise_grading_rules",
    )
    points_for_correct = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=1,
    )
    points_for_blank = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
    )
    points_for_incorrect = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
    )
    minimum_score_threshold = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
    )
    time_to_answer = models.PositiveIntegerField(null=True, blank=True)
    enforce_timeout = models.BooleanField(default=True)
    expected_completion_time = models.PositiveIntegerField(null=True, blank=True)

    # TODO unique constraint [exercise, event]
