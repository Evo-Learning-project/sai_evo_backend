from core.models import UUIDModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Max, Q
from users.models import User

from courses.logic import privileges
from courses.logic.assessment import get_assessor_class

from .managers import (
    EventInstanceManager,
    EventInstanceSlotManager,
    EventManager,
    EventParticipationManager,
    EventTemplateManager,
    EventTemplateRuleManager,
    ExerciseManager,
    ParticipationAssessmentManager,
    ParticipationAssessmentSlotManager,
    ParticipationSubmissionManager,
    ParticipationSubmissionSlotManager,
)


class TimestampableModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SlotNumberedModel(UUIDModel):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="sub_slots",
        on_delete=models.CASCADE,
    )
    slot_number = models.PositiveIntegerField()

    class Meta:
        abstract = True

    @property
    def event(self):
        # shortcut to access the slot's event
        return getattr(self, self.get_container_attribute()).event

    @property
    def participation(self):
        # shortcut to access the slot's participation
        return getattr(self, self.get_container_attribute()).participation

    def get_ancestors(self):
        # returns the slot numbers of all the ancestors of
        # `self` up to the ancestor base slot
        ret = [self.slot_number]
        curr = self
        while curr.parent is not None:
            curr = curr.parent
            ret.append(curr.slot_number)

        return ret

    def get_container_attribute(self):
        # returns the name of the foreign key field to the model that contains the
        # slots (i.e the many-to-one relation with related_name parameter "slots")
        for field in type(self)._meta.get_fields():
            if field.remote_field is not None and field.remote_field.name == "slots":
                return field.name

    def get_sibling_slot(self, sibling_entity, participation_pk=None):
        container = getattr(self, self.get_container_attribute())
        participation = (
            container.participation
            if participation_pk is None
            else container.participations.get(pk=participation_pk)
        )

        # walk up to this slot's base slot and record all the ancestors' slot numbers
        path = reversed(self.get_ancestors())

        related_slot = None
        for step in path:
            # descend the path of ancestors on the related EventInstance,
            # object, starting from the corresponding base slot down to
            # the same level of depth as this slot
            related_slot = getattr(participation, sibling_entity).slots.get(
                parent=related_slot, slot_number=step
            )
        return related_slot


class SideSlotNumberedModel(SlotNumberedModel):
    # TODO find a better name for the class
    class Meta:
        abstract = True

    @property
    def exercise(self):
        return self.get_sibling_slot("event_instance").exercise


class Course(UUIDModel, TimestampableModel):
    name = models.TextField(unique=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="created_courses",
        null=True,
    )
    enrolled_users = models.ManyToManyField(
        "users.User", blank=True
    )  # TODO through model
    hidden = models.BooleanField(default=False)

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


class Exercise(TimestampableModel):
    MULTIPLE_CHOICE_SINGLE_POSSIBLE = 0
    MULTIPLE_CHOICE_MULTIPLE_POSSIBLE = 1
    OPEN_ANSWER = 2
    COMPLETION = 3
    AGGREGATED = 4
    JS = 5
    ATTACHMENT = 6
    # ATTACHMENT_WITH_OPEN_ANSWER

    EXERCISE_TYPES = (
        (MULTIPLE_CHOICE_SINGLE_POSSIBLE, "Multiple choice, single possible"),
        (MULTIPLE_CHOICE_MULTIPLE_POSSIBLE, "Multiple choice, multiple possible"),
        (OPEN_ANSWER, "Open answer"),
        (COMPLETION, "Completion"),
        (AGGREGATED, "Aggregated"),
        (JS, "JavaScript"),
        (ATTACHMENT, "Attachment"),
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
    child_position = models.PositiveIntegerField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    exercise_type = models.PositiveSmallIntegerField(choices=EXERCISE_TYPES)
    label = models.CharField(max_length=75, blank=True)
    text = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    state = models.PositiveSmallIntegerField(choices=EXERCISE_STATES, default=PUBLIC)
    time_to_complete = models.PositiveIntegerField(null=True, blank=True)
    skip_if_timeout = models.BooleanField(default=False)

    objects = ExerciseManager()

    class Meta:
        ordering = [
            "course_id",
            F("parent_id").asc(nulls_first=True),  # base exercises first
            "-created",
            F("child_position").asc(nulls_first=True),
            "pk",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["parent_id", "child_position"],
                condition=Q(parent__isnull=False),
                name="same_parent_unique_child_position",
            )
        ]

    def __str__(self):
        return self.text[:100]

    def clean(self):
        # TODO enforce constraints on the various types of exercise, enforce that if parent is not none, then child_position cannot be none
        pass

    def get_next_child_position(self):
        max_child_position = self.sub_exercises.all().aggregate(
            max_child_position=Max("child_position")
        )["max_child_position"]
        return max_child_position + 1 if max_child_position is not None else 0


class ExerciseChoice(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        related_name="choices",
        on_delete=models.CASCADE,
    )
    text = models.TextField(blank=True)
    score = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
    )
    # correct = models.BooleanField()

    class Meta:
        ordering = ["exercise_id", "pk"]
        constraints = [
            # models.UniqueConstraint(
            #     fields=["exercise_id", "text"],
            #     name="same_exercise_unique_choice_text",
            # )
        ]

    def __str__(self):
        return str(self.exercise) + " - " + self.text[:100]


class ExerciseTestCase(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        related_name="testcases",
        on_delete=models.CASCADE,
    )
    code = models.TextField()
    label = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ["exercise_id", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["exercise_id", "code"],
                name="same_exercise_unique_testcase_code",
            ),
            # models.UniqueConstraint(
            #     fields=["exercise_id", "label"],
            #     name="same_exercise_unique_testcase_label",
            # ),
        ]

    def __str__(self):
        return str(self.exercise) + " - " + self.code


class Event(UUIDModel, TimestampableModel):
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

    EVENT_STATES = (
        (DRAFT, "Draft"),
        (PLANNED, "Planned"),
        (OPEN, "Open"),
        (CLOSED, "Closed"),
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
    event_type = models.PositiveIntegerField(choices=EVENT_TYPES)
    state = models.PositiveIntegerField(choices=EVENT_STATES, default=DRAFT)
    template = models.OneToOneField(
        "EventTemplate",
        on_delete=models.PROTECT,
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
        return self.name

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

    objects = EventTemplateManager()

    class Meta:
        ordering = ["course_id", "pk"]

    def __str__(self):
        return (
            (self.event.name + " template")
            if self.event is not None
            else "--- template"
        )

    def get_next_rule_target_slot_number(self):
        max_rule_target_slot = self.rules.all().aggregate(
            max_target_slot=Max("target_slot_number")
        )["max_target_slot"]
        return max_rule_target_slot + 1 if max_rule_target_slot is not None else 0


class EventTemplateRule(models.Model):
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
    target_slot_number = models.PositiveIntegerField()

    objects = EventTemplateRuleManager()

    class Meta:
        ordering = ["template_id", "target_slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["template_id", "target_slot_number"],
                name="template_unique_target_slot_number",
            )
        ]


class EventTemplateRuleClause(models.Model):
    rule = models.ForeignKey(
        EventTemplateRule,
        related_name="clauses",
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField(Tag)


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

    class Meta:
        ordering = ["event_id", "pk"]


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

    objects = EventInstanceSlotManager()

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

    state = models.PositiveIntegerField(choices=ASSESSMENT_STATES, default=DRAFT)

    # visible_to_student = models.BooleanField(default=False)

    objects = ParticipationAssessmentManager()

    @property
    def event(self):
        # shortcut to access the participation's event
        return self.participation.event

    @property
    def assessment_progress(self):
        slot_states = [s.assessment_state for s in self.slots.all()]
        state = self.NOT_ASSESSED
        for slot_state in slot_states:
            if slot_state == ParticipationAssessmentSlot.ASSESSED:
                state = self.FULLY_ASSESSED
            elif state == self.FULLY_ASSESSED:
                return self.PARTIALLY_ASSESSED
        return state

    class Meta:
        ordering = ["pk"]


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

    objects = ParticipationAssessmentSlotManager()

    class Meta:
        ordering = ["assessment_id", "slot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment_id", "parent_id", "slot_number"],
                name="assessment_unique_slot_number",
            )
        ]

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
    def assessment_state(self):
        return self.ASSESSED if self.score is not None else self.NOT_ASSESSED


class ParticipationSubmission(models.Model):
    objects = ParticipationSubmissionManager()
    # TODO (for events like assignments) have a way to close submissions and possibly re-open them

    class Meta:
        ordering = ["pk"]

    @property
    def current_slots(self):
        ret = self.slots.base_slots()
        if self.event.exercises_shown_at_a_time is not None:
            # slots are among the "current" ones iff their number is between
            # the `current_slot_cursor` of the EventParticipation
            # and the next `exercises_shown_at_a_time` slots
            ret = ret.filter(
                slot_number__gte=self.participation.current_slot_cursor,
                slot_number__lte=(
                    self.participation.current_slot_number
                    + self.event.exercises_shown_at_a_time
                ),
            )
        return ret


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
    attachment = models.FileField(null=True, blank=True)
    # TODO add manytomany to testcases with through model for js exercises

    objects = ParticipationSubmissionSlotManager()

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
        return self in self.submission.current_slots or self.parent.is_in_scope()


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
    state = models.PositiveSmallIntegerField(
        choices=PARTICIPATION_STATES,
        default=IN_PROGRESS,
    )
    current_slot_cursor = models.PositiveIntegerField(null=True, blank=True)

    objects = EventParticipationManager()

    class Meta:
        ordering = ["begin_timestamp", "pk"]

    @property
    def event(self):
        # shortcut to access the participation's event
        return self.event_instance.event

    @property
    def is_cursor_first_position(self):
        return self.current_slot_cursor == 0

    @property
    def is_cursor_last_position(self):
        return (
            self.current_slot_cursor
            >= self.last_slot_number - self.event.exercises_shown_at_a_time
        )

    @property
    def last_slot_number(self):
        return self.slots.base_slots().aggregate(max_slot_number=Max("slot_number"))[
            "max_slot_number"
        ]

    def __str__(self):
        return str(self.event_instance) + " - " + str(self.user)

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)
        # TODO implement
        # qs = EventParticipation.objects.filter(user=self.user)
        # if qs.filter(event_instance__event=self.event_instance.event).exists():
        #     raise ValidationError("A user can only participate in an event once")

    def save(self, *args, **kwargs):
        self.validate_unique()
        super().save(*args, **kwargs)

    def move_current_slot_cursor_forward(self):
        if self.is_cursor_last_position:
            raise ValidationError(
                f"Cursor is past the max position: {self.current_slot_cursor}"
            )

        self.current_slot_cursor += (
            self.event.exercises_shown_at_a_time
        )  # ? max between this and max_slot_number?
        self.save()
        return self.current_slot_cursor

    def move_current_slot_cursor_back(self):
        if self.current_slot_cursor == 0:
            raise ValidationError("Cursor is in position 0")

        self.current_slot_cursor = max(
            self.current_slot_cursor - self.event.exercises_shown_at_a_time, 0
        )
        self.save()
        return self.current_slot_cursor
