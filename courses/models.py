from core.models import HashIdModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Max, Q
from django.utils import timezone
from users.models import User

from courses.logic import privileges
from courses.logic.assessment import get_assessor_class

from .abstract_models import (
    LockableModel,
    OrderableModel,
    SideSlotNumberedModel,
    SlotNumberedModel,
    TimestampableModel,
)
from .managers import (
    CourseManager,
    # EventInstanceManager,
    # EventInstanceSlotManager,
    EventManager,
    EventParticipationManager,
    EventParticipationSlotManager,
    # EventTemplateManager,
    EventTemplateRuleManager,
    ExerciseManager,
    # ParticipationAssessmentManager,
    # ParticipationAssessmentSlotManager,
    # ParticipationSubmissionManager,
    # ParticipationSubmissionSlotManager,
    TagManager,
)


class Course(TimestampableModel):
    name = models.TextField(unique=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_courses",
        null=True,
    )
    hidden = models.BooleanField(default=False)

    objects = CourseManager()

    class Meta:
        ordering = ["-created", "pk"]

    def __str__(self):
        return self.name


class UserCoursePrivilege(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="privileged_courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="privileged_users"
    )
    allow_privileges = models.JSONField(default=list, blank=True)
    deny_privileges = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "course_id"],
                name="same_course_unique_user_permission",
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        privileges.validate_permission_list(self.allow_privileges)
        privileges.validate_permission_list(self.deny_privileges)

    def __str__(self):
        return (
            str(self.user)
            + " - "
            + str(self.course)
            + " - allow: "
            + str(self.allow_privileges)
            + " - deny: "
            + str(self.deny_privileges)
        )


class CourseRole(models.Model):
    name = models.CharField(max_length=250)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    allow_privileges = models.JSONField(default=list)

    class Meta:
        ordering = ["course_id", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["course_id", "name"],
                name="same_course_unique_role_name",
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        privileges.validate_permission_list(self.allow_privileges)

    def __str__(self):
        return (
            str(self.course)
            + " - "
            + self.name
            + " - allow: "
            + str(self.allow_privileges)
        )


class Tag(models.Model):
    course = models.ForeignKey(
        Course,
        null=True,
        blank=True,
        related_name="tags",
        on_delete=models.CASCADE,
    )
    creator = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    name = models.TextField()

    objects = TagManager()

    def __str__(self):
        return str(self.course) + " - " + self.name

    class Meta:
        ordering = ["course_id", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["course_id", "name"],
                name="course_unique_tag_name",
            )
        ]


class Exercise(TimestampableModel, OrderableModel, LockableModel):
    MULTIPLE_CHOICE_SINGLE_POSSIBLE = 0
    MULTIPLE_CHOICE_MULTIPLE_POSSIBLE = 1
    OPEN_ANSWER = 2
    COMPLETION = 3
    AGGREGATED = 4
    JS = 5
    ATTACHMENT = 6
    C = 7
    # ATTACHMENT_WITH_OPEN_ANSWER

    EXERCISE_TYPES = (
        (MULTIPLE_CHOICE_SINGLE_POSSIBLE, "Multiple choice, single possible"),
        (MULTIPLE_CHOICE_MULTIPLE_POSSIBLE, "Multiple choice, multiple possible"),
        (OPEN_ANSWER, "Open answer"),
        (COMPLETION, "Completion"),
        (AGGREGATED, "Aggregated"),
        (JS, "JavaScript"),
        (ATTACHMENT, "Attachment"),
        (C, "C"),
    )

    DRAFT = 0
    PRIVATE = 1
    PUBLIC = 2

    EXERCISE_STATES = (
        (DRAFT, "Draft"),
        (PRIVATE, "Private"),
        (PUBLIC, "Public"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="exercises",
    )
    parent = models.ForeignKey(
        "Exercise",
        null=True,
        blank=True,
        related_name="sub_exercises",
        on_delete=models.CASCADE,
    )
    public_tags = models.ManyToManyField(
        Tag,
        related_name="public_in_exercises",
        blank=True,
    )
    private_tags = models.ManyToManyField(
        Tag,
        related_name="private_in_exercises",
        blank=True,
    )
    exercise_type = models.PositiveSmallIntegerField(choices=EXERCISE_TYPES)
    label = models.CharField(max_length=75, blank=True)
    text = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    initial_code = models.TextField(blank=True)
    state = models.PositiveSmallIntegerField(choices=EXERCISE_STATES, default=DRAFT)
    time_to_complete = models.PositiveIntegerField(null=True, blank=True)
    skip_if_timeout = models.BooleanField(default=False)
    requires_typescript = models.BooleanField(default=False)

    objects = ExerciseManager()

    ORDER_WITH_RESPECT_TO_FIELD = "parent"

    class Meta:
        ordering = [
            "course_id",
            F("parent_id").asc(nulls_first=True),  # base exercises first
            "_ordering",
            "-modified",
            "pk",
        ]
        constraints = [
            # models.UniqueConstraint(
            #     fields=["parent_id", "_ordering"],
            #     condition=Q(parent__isnull=False),
            #     name="same_parent_unique_ordering",
            #     deferrable=models.Deferrable.DEFERRED,
            # )
        ]

    def __str__(self):
        return self.text[:100]

    @property
    def max_score(self):
        # TODO add field to make this writable
        if self.choices.count() == 0:
            return 0

        if self.exercise_type == Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE:
            return sum(
                [max(c.score_selected, c.score_unselected) for c in self.choices.all()]
            )
        if self.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE:
            return max([p for (_, p) in self.get_choices_score_projection().items()])

        return 0

    def clean(self):
        pass

    def get_correct_choices(self):
        """
        Returns the correct choices - the definition depends on the type of exercise.
        For single selection, the correct choices are those with the maximum score projection
        For multiple selection, they are the choices with score_selected greater than
        or equal to score_unselected
        """
        if self.exercise_type == Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE:
            # return all choices whose score_selected is greater than or equal
            # to their score_unselected
            return self.choices.filter(score_selected__gte=F("score_unselected"))
        if self.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE:
            # return all choices that maximize the obtained score
            # when chosen as a single selection
            return [
                c
                for (c, p) in self.get_choices_score_projection().items()
                if p == self.max_score
            ]
        if self.exercise_type == Exercise.COMPLETION:
            return [
                c
                for c in [s.get_correct_choices() for s in self.sub_exercises.all()]
                for c in c
            ]

        return []

    def get_choices_score_projection(self):
        """
        Returns a dictionary in which, to each choice for this exercise, corresponds
        the score obtained by selecting only that choice, i.e. the score_selected attribute
        of that choice plus the sum of the score_unselected attributes for the other choices
        """
        ret = {}
        choices = self.choices.all()
        for c in choices:
            ret[c] = c.score_selected + sum(
                [
                    d.score_unselected
                    for d in [e for e in choices if e.pk != c.pk]  # all other choices
                ]
            )
        return ret


class ExerciseChoice(OrderableModel):
    exercise = models.ForeignKey(
        Exercise,
        related_name="choices",
        on_delete=models.CASCADE,
    )
    text = models.TextField(blank=True)
    score_selected = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
    )
    score_unselected = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
    )
    # correct = models.BooleanField()

    ORDER_WITH_RESPECT_TO_FIELD = "exercise"

    class Meta:
        ordering = ["exercise_id", "_ordering"]
        constraints = [
            models.UniqueConstraint(
                fields=["exercise_id", "_ordering"],
                name="same_exercise_unique_ordering",
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]

    def __str__(self):
        return (
            str(self.exercise)
            + " - "
            + self.text[:100]
            + " (order: "
            + str(self._ordering)
            + ")"
        )


class ExerciseTestCase(OrderableModel):
    SHOW_CODE_SHOW_TEXT = 0
    SHOW_TEXT_ONLY = 1
    HIDDEN = 2

    TESTCASE_TYPES = (
        (SHOW_CODE_SHOW_TEXT, "Show both code and text"),
        (SHOW_TEXT_ONLY, "Show text only"),
        (HIDDEN, "Hidden"),
    )

    exercise = models.ForeignKey(
        Exercise,
        related_name="testcases",
        on_delete=models.CASCADE,
    )
    code = models.TextField(blank=True)  # for js exercises
    stdin = models.TextField(blank=True)  # for c exercises
    expected_stdout = models.TextField(blank=True)  # for c exercises
    text = models.TextField(blank=True)
    testcase_type = models.PositiveIntegerField(
        default=SHOW_CODE_SHOW_TEXT, choices=TESTCASE_TYPES
    )

    ORDER_WITH_RESPECT_TO_FIELD = "exercise"

    class Meta:
        ordering = ["exercise_id", "_ordering"]
        constraints = [
            models.UniqueConstraint(
                fields=["exercise_id", "_ordering"],
                name="same_exercise_unique_ordering_testcase",
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]

    def __str__(self):
        return str(self.exercise) + " - " + self.code


class Event(HashIdModel, TimestampableModel, LockableModel):
    SELF_SERVICE_PRACTICE = 0
    IN_CLASS_PRACTICE = 1
    EXAM = 2
    HOME_ASSIGNMENT = 3
    EXTERNAL = 4

    EVENT_TYPES = (
        (SELF_SERVICE_PRACTICE, "Self-service practice"),
        (IN_CLASS_PRACTICE, "In-class practice"),
        (EXAM, "Exam"),
        (HOME_ASSIGNMENT, "Home assignment"),
        (EXTERNAL, "External resource"),
    )

    DRAFT = 0
    PLANNED = 1
    OPEN = 2
    CLOSED = 3
    RESTRICTED = 4

    EVENT_STATES = (
        (DRAFT, "Draft"),
        (PLANNED, "Planned"),
        (OPEN, "Open"),
        (CLOSED, "Closed"),
        (RESTRICTED, "Restricted"),
    )

    ALLOW_ACCESS = 0
    DENY_ACCESS = 1

    ACCESS_RULES = (
        (ALLOW_ACCESS, "Allow"),
        (DENY_ACCESS, "Deny"),
    )

    name = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="events",
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="created_events",
        on_delete=models.SET_NULL,
    )
    begin_timestamp = models.DateTimeField(null=True, blank=True)
    end_timestamp = models.DateTimeField(null=True, blank=True)
    open_automatically = models.BooleanField(default=True)
    close_automatically = models.BooleanField(default=False)
    event_type = models.PositiveIntegerField(choices=EVENT_TYPES)
    _event_state = models.PositiveIntegerField(
        choices=EVENT_STATES, default=DRAFT, db_column="state"
    )
    template = models.OneToOneField(
        "EventTemplate",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    users_allowed_past_closure = models.ManyToManyField(User, blank=True)
    exercises_shown_at_a_time = models.PositiveIntegerField(null=True, blank=True)
    allow_going_back = models.BooleanField(default=True)
    access_rule = models.PositiveIntegerField(
        choices=ACCESS_RULES, default=ALLOW_ACCESS
    )
    access_rule_exceptions = models.JSONField(default=list, blank=True)

    objects = EventManager()

    def __str__(self):
        return (
            "("
            + str(self.course)
            + ") "
            + (
                (self.name or "_UNNAMED_")
                if self.event_type != self.SELF_SERVICE_PRACTICE
                else "_PRACTICE_"
            )
        )

    class Meta:
        ordering = [
            "course_id",
            "-created",
            "pk",
        ]
        constraints = [
            # TODO disallow duplicates only in non-draft state and with non-empty names
            # models.UniqueConstraint(
            #     fields=["course_id", "name"],
            #     name="event_unique_name_course",
            # )
        ]

    @property
    def state(self):
        now = timezone.localtime(timezone.now())

        if (
            self._event_state == Event.PLANNED
            and self.open_automatically
            and self.begin_timestamp is not None
            and now >= self.begin_timestamp
        ):
            self._event_state = Event.OPEN
            self.save()

        if (
            self._event_state == Event.OPEN
            and self.close_automatically
            and self.end_timestamp is not None
            and now >= self.end_timestamp
        ):
            self._event_state = Event.CLOSED
            self.save()

        if (
            self._event_state == Event.RESTRICTED
            and not self.users_allowed_past_closure.exists()
        ):
            self._event_state = Event.CLOSED
            self.save()

        if (
            self._event_state == Event.RESTRICTED
            and self.users_allowed_past_closure.count()
            == EventParticipation.objects.filter(event_instance__event=self).count()
        ):
            self._event_state = Event.OPEN
            self.save()

        return self._event_state

    @state.setter
    def state(self, value):
        self._event_state = value

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        if not isinstance(self.access_rule_exceptions, list):
            raise ValidationError(
                f"access_rule_exception must be a list, not {self.access_rule_exceptions}"
            )

        for item in self.access_rule_exceptions:
            if not isinstance(item, str):
                raise ValidationError(
                    f"access_rule_exception members must be strings, not {item}"
                )


class EventTemplate(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="event_templates",
    )
    name = models.TextField(blank=True)
    public = models.BooleanField(default=False)
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # objects = EventTemplateManager()

    class Meta:
        ordering = ["course_id", "pk"]

    def __str__(self):
        try:
            return str(self.event)
        except Exception:
            return "-"


class EventTemplateRule(OrderableModel):
    TAG_BASED = 0
    ID_BASED = 1
    FULLY_RANDOM = 2

    RULE_TYPES = (
        (TAG_BASED, "Tag-based rule"),
        (ID_BASED, "Exercise ID-based rule"),
        (FULLY_RANDOM, "Fully random choice"),
    )

    template = models.ForeignKey(
        EventTemplate,
        on_delete=models.CASCADE,
        related_name="rules",
    )
    rule_type = models.PositiveSmallIntegerField(
        choices=RULE_TYPES, null=True, blank=True
    )
    exercises = models.ManyToManyField(
        "courses.Exercise",
        blank=True,
    )

    # how many exercises need to be retrieved using this rule's criteria
    amount = models.PositiveIntegerField(default=1)

    # whether tag-based rules should limit search to the list of public tags in exercises
    search_public_tags_only = models.BooleanField(null=True, blank=True)

    objects = EventTemplateRuleManager()

    ORDER_WITH_RESPECT_TO_FIELD = "template"

    class Meta:
        ordering = ["template_id", "_ordering"]
        constraints = [
            models.UniqueConstraint(
                fields=["template_id", "_ordering"],
                name="same_template_unique_ordering",
                deferrable=models.Deferrable.DEFERRED,
            )
        ]


class EventTemplateRuleClause(models.Model):
    rule = models.ForeignKey(
        EventTemplateRule,
        related_name="clauses",
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField(Tag, blank=True)


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

    # objects = EventInstanceManager()

    class Meta:
        ordering = ["event_id", "pk"]

    def __str__(self):
        return str(self.event) + " " + str(self.pk)

    @property
    def max_score(self):
        exercises = self.exercises.all()
        return sum([e.max_score for e in exercises if e.max_score is not None])


class EventInstanceSlot(SlotNumberedModel):
    event_instance = models.ForeignKey(
        EventInstance,
        related_name="slots",
        on_delete=models.CASCADE,
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
    )

    # objects = EventInstanceSlotManager()

    class Meta:
        ordering = ["event_instance_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["event_instance_id", "parent_id", "slot_number"],
                name="event_instance_unique_slot_number",
            )
        ]

    def get_submission(self, participation):
        return self.get_sibling_slot("submission", participation.pk)

    def get_assessment(self, participation):
        return self.get_sibling_slot("assessment", participation.pk)


class ParticipationAssessment(models.Model):
    """
    Represents the assessment (score, comments) of the participation to an event, either
    issued by a teacher or compiled automatically
    """

    NOT_ASSESSED = 0
    PARTIALLY_ASSESSED = 1
    FULLY_ASSESSED = 2

    ASSESSMENT_PROGRESS_STEPS = (
        (NOT_ASSESSED, "Not assessed"),
        (PARTIALLY_ASSESSED, "Partially assessed"),
        (FULLY_ASSESSED, "Fully assessed"),
    )

    DRAFT = 0
    FOR_REVIEW = 1
    PUBLISHED = 2

    ASSESSMENT_STATES = (
        (DRAFT, "Draft"),
        (FOR_REVIEW, "For review"),
        (PUBLISHED, "Published"),
    )

    _assessment_state = models.PositiveIntegerField(
        choices=ASSESSMENT_STATES,
        default=DRAFT,
        db_column="state",
    )
    _score = models.TextField(  # TODO make string
        # max_digits=5,
        # decimal_places=2,
        null=True,
        blank=True,
    )

    # objects = ParticipationAssessmentManager()

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        try:
            return str(self.participation)
        except Exception:
            return "-"

    @property
    def event(self):
        # shortcut to access the participation's event
        return self.participation.event

    @property
    def base_slots(self):
        return self.slots.base_slots()

    @property
    def assessment_progress(self):
        slot_states = [s.assessment_state for s in self.slots.base_slots()]
        state = self.NOT_ASSESSED
        for slot_state in slot_states:
            if slot_state == ParticipationAssessmentSlot.ASSESSED:
                state = self.FULLY_ASSESSED
            else:
                return self.PARTIALLY_ASSESSED
        return state

    @property
    def state(self):
        if self.event.event_type == Event.SELF_SERVICE_PRACTICE:
            return (
                self.PUBLISHED
                if self.participation.state == EventParticipation.TURNED_IN
                else self.NOT_ASSESSED
            )

        return self._assessment_state

    @state.setter
    def state(self, value):
        self._assessment_state = value

    @property
    def score(self):
        if self._score is None:
            # TODO wrap in string?
            return str(
                sum([s.score if s.score is not None else 0 for s in self.base_slots])
            )
        return self._score

    @score.setter
    def score(self, value):
        self._score = value


class ParticipationAssessmentSlot(SideSlotNumberedModel):
    NOT_ASSESSED = 0
    ASSESSED = 1

    ASSESSMENT_STATES = (
        (NOT_ASSESSED, "Not assessed"),
        (ASSESSED, "Assessed"),
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

    # objects = ParticipationAssessmentSlotManager()

    class Meta:
        ordering = ["assessment_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment_id", "parent_id", "slot_number"],
                name="assessment_unique_slot_number",
            )
        ]

    def __str__(self):
        return str(self.assessment) + " " + str(self.slot_number)

    @property
    def submission(self):
        return self.get_sibling_slot("submission")

    @property
    def score(self):
        if self._score is None:
            return get_assessor_class(self.assessment.participation.event)(
                self
            ).assess()
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def score_edited(self):
        return self._score is not None

    @property
    def assessment_state(self):
        return self.ASSESSED if self.score is not None else self.NOT_ASSESSED


class ParticipationSubmission(models.Model):
    # objects = ParticipationSubmissionManager()
    # TODO (for events like assignments) have a way to close submissions and possibly re-open them

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        try:
            return str(self.participation)
        except Exception:
            return "-"

    @property
    def event(self):
        # shortcut to access the participation's event
        return self.participation.event

    @property
    def current_slots(self):
        ret = self.slots.base_slots()
        if (
            self.event.exercises_shown_at_a_time is not None
            # if the participation has been turned in, show all slots to allow reviewing answers
            and self.participation.state != EventParticipation.TURNED_IN
        ):
            # slots are among the "current" ones iff their number is between
            # the `current_slot_cursor` of the EventParticipation
            # and the next `exercises_shown_at_a_time` slots
            ret = ret.filter(
                slot_number__gte=self.participation.current_slot_cursor,
                slot_number__lt=(
                    self.participation.current_slot_cursor
                    + self.event.exercises_shown_at_a_time
                ),
            )
        return ret


def get_attachment_path(instance, filename):
    event = instance.submission.participation.event_instance.event
    course = event.course
    return f"{course.pk}/{event.pk}/{instance.slot_number}/{filename}"


class ParticipationSubmissionSlot(SideSlotNumberedModel):
    submission = models.ForeignKey(
        ParticipationSubmission,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    seen_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    selected_choices = models.ManyToManyField(
        ExerciseChoice,
        blank=True,
    )
    answer_text = models.TextField(blank=True)
    attachment = models.FileField(null=True, blank=True, upload_to=get_attachment_path)
    execution_results = models.JSONField(blank=True, null=True)

    # objects = ParticipationSubmissionSlotManager()

    class Meta:
        ordering = ["submission_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission_id", "parent_id", "slot_number"],
                name="participation_submission_unique_slot_number",
            )
        ]

    @property
    def event(self):
        # shortcut to access the participation's event
        return self.participation.event

    @property
    def assessment(self):
        return self.get_sibling_slot("assessment")

    def save(self, *args, **kwargs):
        if self.pk is not None:  # can't clean as m2m field won't work without a pk
            # TODO clean the m2m field separately
            self.full_clean()
            if (
                self.selected_choices.exists()
                or bool(self.attachment)
                or bool(self.answer_text)
            ) and self.answered_at is None:
                now = timezone.localtime(timezone.now())
                self.answered_at = now

        return super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        if self.exercise.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE:
            if len(self.answer_text) > 0 or bool(self.attachment):
                raise ValidationError(
                    "Multiple choice questions cannot have an open answer or attachment submission"
                )
        if (
            self.exercise.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE
            and self.selected_choices.count() > 1
        ):
            raise ValidationError(
                "MULTIPLE_CHOICE_SINGLE_POSSIBLE exercise allow only one answer"
            )

        for c in self.selected_choices.all():
            if c not in self.exercise.choices.all():
                raise ValidationError("Invalid choice selected: " + str(c))

    def is_in_scope(self):
        """
        Returns True if the slot is accessible by the user in the corresponding
        EventParticipation, i.e. it contains one of the exercises currently being
        shown to the user; False otherwise
        """
        return (
            self in self.submission.current_slots
            or self.parent is not None
            and self.parent.is_in_scope()
        )


class EventParticipation(models.Model):
    IN_PROGRESS = 0
    TURNED_IN = 1
    PARTICIPATION_STATES = (
        (IN_PROGRESS, "In progress"),
        (TURNED_IN, "Turned in"),
    )

    NOT_ASSESSED = 0
    PARTIALLY_ASSESSED = 1
    FULLY_ASSESSED = 2
    ASSESSMENT_PROGRESS_STEPS = (
        (NOT_ASSESSED, "Not assessed"),
        (PARTIALLY_ASSESSED, "Partially assessed"),
        (FULLY_ASSESSED, "Fully assessed"),
    )

    DRAFT = 0
    FOR_REVIEW = 1
    PUBLISHED = 2
    ASSESSMENT_STATES = (
        (DRAFT, "Draft"),
        (FOR_REVIEW, "For review"),
        (PUBLISHED, "Published"),
    )

    # relations
    user = models.ForeignKey(
        User,
        related_name="participations",
        on_delete=models.PROTECT,
    )
    event = models.ForeignKey(  # TODO make non nullable when you complete migration
        Event,
        null=True,
        related_name="participations",
        on_delete=models.PROTECT,
    )

    # !! temporary
    event_instance = models.ForeignKey(
        EventInstance,
        null=True,
        blank=True,
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
    #!!

    # bookkeeping fields
    begin_timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True, blank=True)
    state = models.PositiveSmallIntegerField(
        choices=PARTICIPATION_STATES,
        default=IN_PROGRESS,
    )
    current_slot_cursor = models.PositiveIntegerField(default=0)

    # assessment fields
    _assessment_state = models.PositiveIntegerField(
        choices=ASSESSMENT_STATES,
        default=DRAFT,
    )
    _score = models.TextField(blank=True, null=True)

    objects = EventParticipationManager()

    class Meta:
        ordering = ["event_id", "-begin_timestamp", "pk"]
        # TODO enforce user_id, event_id pair uniqueness

    def __str__(self):
        return str(self.event) + " - " + str(self.user)

    @property
    def is_cursor_first_position(self):
        return self.current_slot_cursor == 0

    @property
    def is_cursor_last_position(self):
        if self.event.exercises_shown_at_a_time is None:
            return True

        return (
            self.current_slot_cursor
            > self.last_slot_number - self.event.exercises_shown_at_a_time
        )

    @property
    def last_slot_number(self):
        return self.prefetched_base_slots.aggregate(max_slot_number=Max("slot_number"))[
            "max_slot_number"
        ]

    @property
    def max_score(self):
        return 0
        # TODO re-implement
        # exercises = self.exercises.all()
        # return sum([e.max_score for e in exercises if e.max_score is not None])

    @property
    def assessment_progress(self):
        slot_states = [s.assessment_state for s in self.prefetched_base_slots]
        state = self.NOT_ASSESSED
        for slot_state in slot_states:
            if slot_state == ParticipationAssessmentSlot.ASSESSED:
                state = self.FULLY_ASSESSED
            else:
                return self.PARTIALLY_ASSESSED
        return state

    @property
    def assessment_visibility(self):
        if self.event.event_type == Event.SELF_SERVICE_PRACTICE:
            return (
                self.PUBLISHED
                if self.participation.state == EventParticipation.TURNED_IN
                else self.NOT_ASSESSED
            )
        return self._assessment_state

    @assessment_visibility.setter
    def assessment_visibility(self, value):
        self._assessment_state = value

    @property
    def is_assessment_available(self):
        return self.assessment_visibility == EventParticipation.PUBLISHED

    @property
    def score(self):
        if self._score is None:
            return str(
                sum(
                    [
                        s.score if s.score is not None else 0
                        for s in self.prefetched_base_slots
                    ]
                )
            )
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def score_edited(self):
        return self._score is not None and len(self._score) > 0

    @property
    def current_slots(self):
        ret = self.prefetched_base_slots
        if (
            self.event.exercises_shown_at_a_time is not None
            # if the participation has been turned in, show all slots to allow reviewing answers
            and self.state != EventParticipation.TURNED_IN
        ):
            # slots are among the "current" ones iff their number is between the `current_slot_cursor`
            # of the EventParticipation and the next `exercises_shown_at_a_time` slots
            ret = ret.filter(
                slot_number__gte=self.current_slot_cursor,
                slot_number__lt=(
                    self.current_slot_cursor + self.event.exercises_shown_at_a_time
                ),
            )
        return ret

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)
        # TODO implement
        # qs = EventParticipation.objects.filter(user=self.user)
        # if qs.filter(event_instance__event=self.event_instance.event).exists():
        #     raise ValidationError("A user can only participate in an event once")

    def save(self, *args, **kwargs):
        self.validate_unique()
        if self.state == EventParticipation.TURNED_IN and self.end_timestamp is None:
            self.end_timestamp = timezone.localtime(timezone.now())
        super().save(*args, **kwargs)

    def move_current_slot_cursor_forward(self):
        if self.is_cursor_last_position:
            raise ValidationError(
                f"Cursor is past the max position: {self.current_slot_cursor}"
            )

        self.current_slot_cursor += (
            self.event.exercises_shown_at_a_time
        )  # ? max between this and max_slot_number?
        self.save(update_fields=["current_slot_cursor"])

        # mark new current slot as seen
        now = timezone.localtime(timezone.now())
        current_slot = self.slots.prefetched_base_slots.get(
            slot_number=self.current_slot_cursor
        )
        if current_slot.seen_at is None:
            current_slot.seen_at = now
            current_slot.save(update_fields=["seen_at"])

        return self.current_slot_cursor

    def move_current_slot_cursor_back(self):
        if self.current_slot_cursor == 0:
            raise ValidationError("Cursor is in position 0")

        self.current_slot_cursor = max(
            self.current_slot_cursor - self.event.exercises_shown_at_a_time, 0
        )
        self.save(update_fields=["current_slot_cursor"])
        return self.current_slot_cursor


class EventParticipationSlot(models.Model):
    NOT_ASSESSED = 0
    ASSESSED = 1
    ASSESSMENT_STATES = (
        (NOT_ASSESSED, "Not assessed"),
        (ASSESSED, "Assessed"),
    )

    # relations
    participation = models.ForeignKey(
        EventParticipation,
        related_name="slots",
        on_delete=models.CASCADE,
    )
    exercise = models.ForeignKey(
        Exercise,
        related_name="in_slots",
        on_delete=models.CASCADE,
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="sub_slots",
        on_delete=models.CASCADE,
    )

    # bookkeeping fields
    slot_number = models.PositiveIntegerField()
    seen_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    # submission fields
    selected_choices = models.ManyToManyField(
        ExerciseChoice,
        blank=True,
    )
    answer_text = models.TextField(blank=True)
    attachment = models.FileField(
        null=True,
        blank=True,
        upload_to=get_attachment_path,
    )
    execution_results = models.JSONField(blank=True, null=True)

    # assessment fields
    comment = models.TextField(blank=True)
    _score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    objects = EventParticipationSlotManager()

    class Meta:
        ordering = ["participation_id", "parent_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["participation_id", "parent_id", "slot_number"],
                name="event_participation_unique_slot_number",
            )
        ]

    def __str__(self):
        return str(self.participation) + " " + str(self.slot_number)

    @property
    def score(self):
        if self._score is None:
            return get_assessor_class(self.participation.event)(self).assess()
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def score_edited(self):
        return self._score is not None

    @property
    def assessment_state(self):
        return self.ASSESSED if self.score is not None else self.NOT_ASSESSED

    def save(self, *args, **kwargs):
        if self.pk is not None:  # can't clean as m2m field won't work without a pk
            # TODO clean the m2m field separately
            self.full_clean()
            if (
                self.selected_choices.exists()
                or bool(self.attachment)
                or bool(self.answer_text)
            ) and self.answered_at is None:
                now = timezone.localtime(timezone.now())
                self.answered_at = now

        return super().save(*args, **kwargs)

    # TODO clean

    def is_in_scope(self):
        """
        Returns True if the slot is accessible by the user in the corresponding
        EventParticipation, i.e. it contains one of the exercises currently being
        shown to the user; False otherwise
        """
        return (
            self in self.participation.current_slots
            or self.parent is not None
            and self.parent.is_in_scope()
        )
