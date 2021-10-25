from django.db import models
from users.models import User

from .logic.grading import apply_grading_rule


class Course(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_courses",
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
        (MULTIPLE_CHOICE_SINGLE_POSSIBLE, "Multiple choice single possible"),
        (MULTIPLE_CHOICE_MULTIPLE_POSSIBLE, "Multiple choice multiple possible"),
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
    )
    tags = models.ManyToManyField("tags.Tag", blank=True)
    exercise_type = models.PositiveSmallIntegerField(choices=EXERCISE_TYPES)
    text = models.TextField()
    solution = models.TextField(blank=True)
    draft = models.BooleanField(default=False)

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

    EVENT_TYPES = (
        (SELF_SERVICE_PRACTICE, "Self-service practice"),
        (IN_CLASS_PRACTICE, "In-class practice"),
        (EXAM, "Exam"),
        (ASSIGNMENT, "Assignment"),
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
        "EventTemplate", related_name="events", on_delete=models.PROTECT
    )

    def __str__(self):
        return self.name

    # TODO unique [course, name]


class EventParticipation(models.Model):
    IN_PROGRESS = 0
    TURNED_IN = 1
    AWAITING_MANUAL_GRADING = 2
    GRADED = 3

    PARTICIPATION_STATES = (
        (IN_PROGRESS, "In progress"),
        (TURNED_IN, "Turned in"),
        (AWAITING_MANUAL_GRADING, "Awaiting manual grading"),
        (GRADED, "Graded"),
    )

    event = models.ForeignKey(
        Event,
        related_name="participations",
        on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        User,
        related_name="events",
        on_delete=models.PROTECT,
    )
    begin_timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True, blank=True)
    state = models.PositiveSmallIntegerField(choices=PARTICIPATION_STATES)
    assigned_exercises = models.ManyToManyField(Exercise, through="AssignedExercise")
    current_exercise_cursor = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.event) + " - " + str(self.user)

    @property
    def current_exercise(self):
        return self.assigned_exercises.get(position=self.current_exercise_cursor)


class AssignedExercise(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.SET_NULL)
    participation = models.ForeignKey(EventParticipation, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    selected_choice = models.ForeignKey(ExerciseChoice, null=True, blank=True)
    answer_text = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    _score = models.DecimalField(decimal_places=2)

    @property
    def score(self):
        if self._score is None:
            return apply_grading_rule(self)
        return self._score

    @score.setter
    def score(self, value):
        self._score = value


class ExerciseGradingRule(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="exercise_grading_rules",
    )
    points_for_correct = models.DecimalField(decimal_places=2)
    points_for_blank = models.DecimalField(decimal_places=2)
    points_for_incorrect = models.DecimalField(decimal_places=2)
    minimum_score_threshold = models.DecimalField(decimal_places=2)
    time_to_answer = models.PositiveIntegerField(null=True, blank=True)
    enforce_timeout = models.BooleanField(default=True)
    expected_completion_time = models.PositiveIntegerField(null=True, blank=True)

    # TODO unique constraint [exercise, event]
