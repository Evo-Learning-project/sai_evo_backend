from decimal import Decimal
from content.models import Content, PostModel, VoteModel
from core.models import HashIdModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Max, Q
from django.utils import timezone
from demo_mode.logic import is_demo_mode
from demo_mode.querysets import DemoCoursesQuerySet
from gamification.actions import (
    CORRECTLY_ANSWERED_EXERCISE,
    EXERCISE_SOLUTION_APPROVED,
    EXERCISE_SOLUTION_DOWNVOTE_DELETED,
    EXERCISE_SOLUTION_DOWNVOTED,
    EXERCISE_SOLUTION_UPVOTE_DELETED,
    EXERCISE_SOLUTION_UPVOTED,
    SUBMIT_EXERCISE_SOLUTION,
    SUBMIT_FIRST_EXERCISE_SOLUTION,
    TURN_IN_PRACTICE_PARTICIPATION,
)
import json
from gamification.entry import get_gamification_engine
from users.models import User
from django.db import transaction
from django.db.models import Sum, Case, When, Value
from django_lifecycle import (
    LifecycleModel,
    LifecycleModelMixin,
    hook,
    BEFORE_UPDATE,
    AFTER_UPDATE,
    AFTER_CREATE,
    BEFORE_DELETE,
)

from courses import signals  # to make signals work

import logging

logger = logging.getLogger(__name__)


from courses.logic import privileges
from courses.logic.assessment import get_assessor_class

from .abstract_models import (
    LockableModel,
    OrderableModel,
    TimestampableModel,
)
from .managers import (
    CourseManager,
    EventManager,
    EventParticipationManager,
    EventParticipationSlotManager,
    EventTemplateRuleManager,
    ExerciseManager,
    ExerciseSolutionManager,
    TagManager,
)


# TODO change name to get_participation_slot_attachment_path
def get_attachment_path(slot, filename):
    event = slot.participation.event
    course = event.course
    return f"{course.pk}/{event.pk}/{slot.slot_number}/{filename}"


def get_testcase_attachment_path(testcase_attachment, filename):
    testcase = testcase_attachment.testcase
    exercise = testcase.exercise
    course = exercise.course
    return f"{course.pk}/testcase_attachments/{exercise.pk}/{testcase.pk}/{filename}"


class Course(TimestampableModel):
    """
    Courses are at the top level of the model hierarchy. Everything happens
    in the context of a course. A course is created by a teacher and managed
    by one or more users with permissions. A course contains exercises, and
    allows teachers to create exams (see model Event) and students to practice
    using the available exercises
    """

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

    if is_demo_mode():
        demo_manager = DemoCoursesQuerySet.as_manager()

    class Meta:
        ordering = ["-created", "pk"]

    def __str__(self):
        return self.name


class UserCoursePrivilege(models.Model):
    """
    Represents the administrative permissions a user has over a course.
    See logic.privileges.py for the available permissions.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="privileged_courses",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="privileged_users",
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
    """
    Reusable permission group for users inside of a course
    """

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
    """
    Used to tag exercises (see Exercise model)
    """

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
    """
    An Exercise represents a question, coding problem, or other element that
    can appear inside of an exam. It can be PRIVATE or PUBLIC, depending on
    whether the teachers want students to be able to freely access it, and is
    associated with some public tags and private tags.
    Exercises can contain other exercises.
    """

    MULTIPLE_CHOICE_SINGLE_POSSIBLE = 0
    MULTIPLE_CHOICE_MULTIPLE_POSSIBLE = 1
    OPEN_ANSWER = 2
    COMPLETION = 3
    AGGREGATED = 4
    JS = 5
    ATTACHMENT = 6
    C = 7
    PYTHON = 8
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
        (PYTHON, "Python"),
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
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="created_exercises",
        on_delete=models.SET_NULL,
    )
    # for AGGREGATED or COMPLETION exercises
    parent = models.ForeignKey(
        "Exercise",
        null=True,
        blank=True,
        related_name="sub_exercises",
        on_delete=models.CASCADE,
    )
    # how much the sub-exercise weighs in scoring the parent exercise
    child_weight = models.PositiveSmallIntegerField(default=1)
    # tags publicly visible by students
    public_tags = models.ManyToManyField(
        Tag,
        related_name="public_in_exercises",
        blank=True,
    )
    # tags hidden from students
    private_tags = models.ManyToManyField(
        Tag,
        related_name="private_in_exercises",
        blank=True,
    )
    exercise_type = models.PositiveSmallIntegerField(choices=EXERCISE_TYPES)
    # mnemonic name for the exercise
    label = models.CharField(max_length=75, blank=True)
    text = models.TextField(blank=True)

    solution = models.TextField(blank=True)  # TODO delete once implemented new feature
    initial_code = models.TextField(blank=True)  # TODO implement

    state = models.PositiveSmallIntegerField(choices=EXERCISE_STATES, default=DRAFT)

    # currently unused
    time_to_complete = models.PositiveIntegerField(null=True, blank=True)
    skip_if_timeout = models.BooleanField(default=False)

    # only relevant if exercise_type is JS
    requires_typescript = models.BooleanField(default=False)
    # if True, an answer that gets a score less than the max score for the exercise gets 0 instead
    all_or_nothing = models.BooleanField(default=False)

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
            # TODO review
            # models.UniqueConstraint(
            #     fields=["parent_id", "_ordering"],
            #     condition=Q(parent__isnull=False),
            #     name="same_parent_unique_ordering",
            #     deferrable=models.Deferrable.DEFERRED,
            # )
        ]

    def __str__(self):
        return self.text[:100]

    def clean(self):
        pass

    def get_max_score(self):
        if self.exercise_type in [Exercise.OPEN_ANSWER, Exercise.ATTACHMENT]:
            return None
        if self.exercise_type in [Exercise.AGGREGATED, Exercise.COMPLETION]:
            return sum(
                [
                    Decimal(s.get_max_score() or 0) * Decimal(s.child_weight or 0)
                    for s in self.sub_exercises.all()
                ]
            )
        if self.exercise_type in [Exercise.JS, Exercise.C, Exercise.PYTHON]:
            return self.testcases.count()
        if self.exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE:
            if hasattr(self, "prefetched_max_choice_correctness"):
                max_score = self.prefetched_max_choice_correctness
            else:
                # logger.warning(
                #     "no prefetched_max_choice_correctness for exercise with id "
                #     + str(self.pk)
                # )
                max_score = (self.choices.all().aggregate(Max("correctness")))[
                    "correctness__max"
                ]  # TODO `or 0`?
            return max_score
        if self.exercise_type == Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE:
            correct_choices = self.choices.filter(correctness__gt=0)
            return sum([c.correctness for c in correct_choices])

        assert False, f"max_score not defined for type {self.exercise_type}"


class ExerciseSolution(LifecycleModelMixin, TimestampableModel):
    """
    A solution to an exercise created by a user
    """

    DRAFT = 0
    SUBMITTED = 1
    PUBLISHED = 2
    REJECTED = 3

    STATES = (
        (DRAFT, "Draft"),
        (SUBMITTED, "Submitted"),
        (PUBLISHED, "Published"),
        (REJECTED, "Rejected"),
    )

    exercise = models.ForeignKey(
        Exercise, related_name="solutions", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name="solutions",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    _content = models.ForeignKey(Content, on_delete=models.PROTECT)
    state = models.PositiveSmallIntegerField(choices=STATES, default=DRAFT)

    bookmarked_by = models.ManyToManyField(
        User,
        blank=True,
        related_name="bookmarked_exercise_solutions",
    )

    objects = ExerciseSolutionManager()

    class Meta:
        ordering = ["exercise_id", "created"]

    def __str__(self):
        return (
            str(self.user or "Anon")
            + " "
            + str(self.exercise.pk)
            + ": "
            + str(self.content)
        )

    @property
    def score(self):
        return (
            self.votes.all()
            .annotate(
                value=Case(
                    When(vote_type=VoteModel.DOWN_VOTE, then=Value(-1)),
                    When(vote_type=VoteModel.UP_VOTE, then=Value(1)),
                    default=Value(0),
                    output_field=models.SmallIntegerField(),
                )
            )
            .aggregate(score=Sum("value", default=0))["score"]
        )

    @property
    def content(self):
        return self._content.text_content

    @content.setter
    def content(self, val):
        self._content.text_content = val
        self._content.save()

    @hook(AFTER_UPDATE, when="state", was=DRAFT, is_now=SUBMITTED)
    def on_submit(self):
        is_first_public_solution = (
            not self.exercise.solutions.all()
            .exclude_draft_and_rejected()
            .exclude(pk=self.pk)
            .exists()
        )
        # two different action codes are dispatched depending on whether
        # or not this is the first solution submitted for the exercise
        action_code = (
            SUBMIT_FIRST_EXERCISE_SOLUTION
            if is_first_public_solution
            else SUBMIT_EXERCISE_SOLUTION
        )
        get_gamification_engine().dispatch_action(
            {
                "action": action_code,
                "main_object": self,
                "related_objects": [self.exercise.course, self.exercise],
                "user": self.user,
                "extras": {},
            }
        )

    @hook(AFTER_UPDATE, when="state", changes_to=PUBLISHED)
    def on_approve(self):
        get_gamification_engine().dispatch_action(
            {
                "action": EXERCISE_SOLUTION_APPROVED,
                "main_object": self,
                "related_objects": [self.exercise.course, self.exercise],
                "user": self.user,
                "extras": {},
            }
        )


class ExerciseSolutionComment(PostModel):
    solution = models.ForeignKey(
        ExerciseSolution,
        related_name="comments",
        on_delete=models.PROTECT,
    )


class ExerciseSolutionVote(LifecycleModelMixin, VoteModel):
    solution = models.ForeignKey(
        ExerciseSolution,
        related_name="votes",
        on_delete=models.PROTECT,
    )

    @hook(AFTER_CREATE)
    def on_create(self):
        action_code = (
            EXERCISE_SOLUTION_UPVOTED
            if self.vote_type == self.UP_VOTE
            else EXERCISE_SOLUTION_DOWNVOTED
        )
        get_gamification_engine().dispatch_action(
            {
                "action": action_code,
                "main_object": self,
                "related_objects": [self.solution.exercise.course],
                "user": self.solution.user,
                "extras": {},
            }
        )

    @hook(BEFORE_DELETE)
    def on_delete(self):
        action_code = (
            EXERCISE_SOLUTION_UPVOTE_DELETED
            if self.vote_type == self.UP_VOTE
            else EXERCISE_SOLUTION_DOWNVOTE_DELETED
        )
        get_gamification_engine().dispatch_action(
            {
                "action": action_code,
                "main_object": self,
                "related_objects": [self.solution.exercise.course],
                "user": self.solution.user,
                "extras": {},
            }
        )

    # TODO handle vote update


class ExerciseChoice(OrderableModel):
    """
    A selectable choice in a multiple-choice exercise
    """

    exercise = models.ForeignKey(
        Exercise,
        related_name="choices",
        on_delete=models.CASCADE,
    )
    text = models.TextField(blank=True)
    correctness = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
    )

    ORDER_WITH_RESPECT_TO_FIELD = "exercise"

    class Meta:
        ordering = ["exercise_id", "_ordering"]
        constraints = [
            models.UniqueConstraint(
                fields=["exercise_id", "_ordering"],
                name="same_exercise_unique_ordering",
                deferrable=models.Deferrable.DEFERRED,
            ),
            # TODO add uniqueness for the choice text
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

    # def save(self, *args, **kwargs):
    #     # TODO resolve conflict with _ordering field, which is non-nullable
    #     # self.full_clean()
    #     return super().save(*args, **kwargs)

    # def clean(self, *args, **kwargs):
    #     if self.correctness_percentage is not None and (
    #         self.correctness_percentage > 100 or self.correctness_percentage < -100
    #     ):
    #         raise ValidationError(
    #             f"invalid correctness_percentage value {self.access_rule_exceptions}"
    #         )


class ExerciseTestCase(OrderableModel):
    """
    A test case used to evaluate an answer to a programming exercise
    """

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

    code = models.TextField(blank=True)  # for js and python exercises

    stdin = models.TextField(blank=True)  # for c exercises
    expected_stdout = models.TextField(blank=True)  # for c exercises

    # human-readable description of what the test case does
    text = models.TextField(blank=True)

    testcase_type = models.PositiveIntegerField(
        default=SHOW_CODE_SHOW_TEXT, choices=TESTCASE_TYPES
    )

    ORDER_WITH_RESPECT_TO_FIELD = "exercise"

    MAX_CODE_LENGTH = 2000

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

    @property
    def truncated_code(self):
        """
        Returns a truncated version of the test case code.
        Used to keep large test cases from generating huge responses
        """
        if len(self.code) < self.MAX_CODE_LENGTH:
            return self.code

        return self.code[: self.MAX_CODE_LENGTH] + "<...>"

    @property
    def truncated_stdin(self):
        """
        Returns a truncated version of the test case stdin.
        Used to keep large test cases from generating huge responses
        """
        if len(self.stdin) < self.MAX_CODE_LENGTH:
            return self.stdin

        return self.stdin[: self.MAX_CODE_LENGTH] + "<...>"

    @property
    def truncated_expected_stdout(self):
        """
        Returns a truncated version of the test case expected stdout.
        Used to keep large test cases from generating huge responses
        """
        if len(self.expected_stdout) < self.MAX_CODE_LENGTH:
            return self.expected_stdout

        return self.expected_stdout[: self.MAX_CODE_LENGTH] + "<...>"


class ExerciseTestCaseAttachment(models.Model):
    testcase = models.ForeignKey(
        ExerciseTestCase,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    attachment = models.FileField(
        null=True,
        blank=True,
        upload_to=get_testcase_attachment_path,
    )


class Event(HashIdModel, TimestampableModel, LockableModel):
    """
    An Event represents some type of quiz/exam students can participate in.
    Teachers can create exam events, and students can create "self-service
    practice" events (i.e. a simulation of an exam).
    See the EventTemplate model for how exercises are related to events.
    """

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

    NO_TIME_LIMIT = 0
    TIME_LIMIT = 1
    TIME_LIMIT_RULES = (
        (NO_TIME_LIMIT, "No time limit"),
        (TIME_LIMIT, "Time limit"),
    )

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
    name = models.TextField(blank=True)

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

    # exam specific settings
    instructions = models.TextField(blank=True)
    begin_timestamp = models.DateTimeField(null=True, blank=True)
    end_timestamp = models.DateTimeField(null=True, blank=True)
    open_automatically = models.BooleanField(default=True)
    close_automatically = models.BooleanField(default=False)
    users_allowed_past_closure = models.ManyToManyField(User, blank=True)
    exercises_shown_at_a_time = models.PositiveIntegerField(null=True, blank=True)
    allow_going_back = models.BooleanField(default=True)
    access_rule = models.PositiveIntegerField(  # TODO positive small integer
        choices=ACCESS_RULES, default=ALLOW_ACCESS
    )
    access_rule_exceptions = models.JSONField(default=list, blank=True)
    time_limit_rule = models.PositiveSmallIntegerField(
        choices=TIME_LIMIT_RULES, default=NO_TIME_LIMIT
    )
    time_limit_seconds = models.PositiveIntegerField(null=True, blank=True)
    time_limit_exceptions = models.JSONField(default=list, blank=True)
    randomize_rule_order = models.BooleanField(default=False)

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
    def max_score(self):
        rules = self.template.rules.all()
        return sum([(r.weight or 0) * r.amount for r in rules])

    # TODO remove as this is unused
    @max_score.setter
    def max_score(self, value):
        # divides the given value evenly among the template
        # rules and sets it as their weight property
        rules = self.template.rules.all()
        per_rule_value = value / sum([r.amount for r in rules])
        rules.update(weight=per_rule_value)

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
            and self.users_allowed_past_closure.count() == self.participations.count()
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
        if not isinstance(self.time_limit_exceptions, list):
            raise ValidationError(
                f"time_limit_exceptions must be a list, not {self.access_rule_exceptions}"
            )
        for item in self.time_limit_exceptions:
            # time_limit_exceptions must be a list of lists, each with
            # length 2, where the first element is a string (the email
            # address of a student) and the second a string or number
            # (the number of seconds amounting to the time limit for
            # that student)
            if not isinstance(item, list):
                raise ValidationError(
                    f"time_limit_exceptions members must be lists, not {item}"
                )
            if len(item) != 2:
                raise ValidationError(f"{item} must have length 2")
            if not isinstance(item[0], str):
                raise ValidationError(f"{item[0]} must be a string")
            if type(item[1]) not in (str, int, float):
                raise ValidationError(f"{item[1]} must be a string or number")

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
    """
    An EventTemplate defines a set of rules (see model EventTemplateRule) that dictate how
    exercises should be assigned to participants in an event (see model EventParticipation).
    """

    course = models.ForeignKey(  # TODO this is redundant; remove
        Course,
        on_delete=models.CASCADE,
        related_name="event_templates",
    )
    name = models.TextField(blank=True)  # currently unused
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
    """
    An EventTemplateRule defines what exercises can be assigned to a specific
    slot (see model EventParticipationSlot) of a participation to an event.
    A rule specifies an amount of exercises that can be picked by the rule,
    and some criteria for how to select those exercises.
    A rule can currently be of three kinds:
    1. Fully random - pick `amount` random exercises
    2. ID-based - pick `amount` exercises that are in the `exercises` m2m relation
    3. Tag-based - pick `amount` exercises whose tags satisfy the query created by the
    clauses of this rule: see the EventTemplateRuleClause model to see how this works.
    """

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

    # for ID-based rules
    exercises = models.ManyToManyField(
        "courses.Exercise",
        blank=True,
    )

    # weight of the targeted slot(s), i.e. the maximum score for the related exercise(s)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
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

    # TODO enforce constraints such as: for ID-based rules, self.amount <= len(self.exercises)


class EventTemplateRuleClause(models.Model):
    """
    An EventTemplateRuleClause is a specifies a list of tags of interest.
    When an EventTemplateRule is tag-based and has a list of clauses, say
    c1, c2, c3, the condition generated by that rule is the following:

    pick `amount` (the rule amount) exercises that have:
    at least one tag from c1 AND
    at least one tag from c2 AND
    at least one tag from c3.

    So the tags in m2m field `tags` are "OR'd" and the clauses are "AND'd".
    """

    rule = models.ForeignKey(
        EventTemplateRule,
        related_name="clauses",
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        ordering = ["rule_id", "id"]


class EventParticipation(LifecycleModelMixin, models.Model):
    """
    A participation of a user to an event.

    A participation has a state, which determines if the user is still participating
    or has turned in / abandoned, and has an assessment state, which determines
    whether a teacher has graded the answers given yet.

    """

    IN_PROGRESS = 0
    TURNED_IN = 1
    # TODO implement ABANDONED state
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

    # bookkeeping fields
    begin_timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True, blank=True)
    state = models.PositiveSmallIntegerField(
        choices=PARTICIPATION_STATES,
        default=IN_PROGRESS,
    )
    current_slot_cursor = models.PositiveIntegerField(default=0)
    bookmarked = models.BooleanField(default=False)

    # assessment fields
    _assessment_state = models.PositiveIntegerField(
        choices=ASSESSMENT_STATES,
        default=DRAFT,
    )
    _score = models.TextField(blank=True, null=True)

    objects = EventParticipationManager()

    class Meta:
        ordering = ["event_id", "-begin_timestamp", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["event_id", "user_id"],
                name="event_participation_unique_user",
            )
        ]

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
    def base_slots(self):
        if hasattr(self, "prefetched_base_slots"):
            # print([s.slot_number for s in self.prefetched_base_slots])
            # TODO review for nested slots
            base_slots = sorted(self.prefetched_base_slots, key=lambda s: s.slot_number)
        else:
            base_slots = self.slots.base_slots()
        return base_slots

    @property
    def last_slot_number(self):
        return len(self.base_slots) - 1

    @property
    def assessment_progress(self):
        slot_states = [s.assessment_state for s in self.base_slots]
        state = self.NOT_ASSESSED
        for slot_state in slot_states:
            if slot_state == EventParticipationSlot.ASSESSED:
                state = self.FULLY_ASSESSED
            else:
                return self.PARTIALLY_ASSESSED
        return state

    @property
    def assessment_visibility(self):
        if self.event.event_type == Event.SELF_SERVICE_PRACTICE:
            return (
                self.PUBLISHED
                if self.state == EventParticipation.TURNED_IN
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
                round(
                    sum(
                        [s.score if s.score is not None else 0 for s in self.base_slots]
                    ),
                    2,
                ),
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
        ret = self.base_slots
        if (
            self.event.exercises_shown_at_a_time is not None
            # if the participation has been turned in, show all slots to allow reviewing answers
            and self.state != EventParticipation.TURNED_IN
        ):
            # slots are among the "current" ones iff their number is between the `current_slot_cursor`
            # of the EventParticipation and the next `exercises_shown_at_a_time` slots
            ret = (
                ret.filter(
                    slot_number__gte=self.current_slot_cursor,
                    slot_number__lt=(
                        self.current_slot_cursor + self.event.exercises_shown_at_a_time
                    ),
                )
                if not isinstance(ret, list)
                else [
                    s
                    for s in ret
                    if s.slot_number >= self.current_slot_cursor
                    and s.slot_number
                    < self.current_slot_cursor + self.event.exercises_shown_at_a_time
                ]
            )
        return ret

    def save(self, *args, **kwargs):
        # TODO use django lifecycle package
        if self.state == EventParticipation.TURNED_IN and self.end_timestamp is None:
            self.end_timestamp = timezone.localtime(timezone.now())
        super().save(*args, **kwargs)

    @hook(AFTER_UPDATE, when="state", changes_to=TURNED_IN)
    def on_turn_in(self):
        if self.event.event_type == Event.SELF_SERVICE_PRACTICE:
            get_gamification_engine().dispatch_action(
                {
                    "action": TURN_IN_PRACTICE_PARTICIPATION,
                    "main_object": self,
                    "related_objects": [self.event.course],
                    "user": self.user,
                    "extras": {},
                }
            )
            # for each correctly-answered exercise, dispatch an action
            for slot in self.slots.base_slots():
                # TODO review
                # max score obtained for this exercise
                if (
                    slot.populating_rule is not None  # for backward compatibility
                    and slot.score == slot.populating_rule.weight
                ):
                    get_gamification_engine().dispatch_action(
                        {
                            "action": CORRECTLY_ANSWERED_EXERCISE,
                            "main_object": slot.exercise,
                            "related_objects": [self.event.course, self, slot],
                            "user": self.user,
                            "extras": {},  # TODO might put exercise tags or other information to create more complex goals
                        }
                    )

    def move_current_slot_cursor_forward(self):
        if self.is_cursor_last_position:
            raise ValidationError(
                f"Cursor is past the max position: {self.current_slot_cursor}"
            )

        if self.event.exercises_shown_at_a_time is None:
            raise ValidationError("Event shows all exercises at once")

        # ? add min between this exercises_shown_at_a_time and max_slot_number?
        self.current_slot_cursor += self.event.exercises_shown_at_a_time
        self.save(update_fields=["current_slot_cursor"])

        # TODO use django lifecycle package
        # mark new current slot as seen
        current_slot = [
            s for s in self.base_slots if s.slot_number == self.current_slot_cursor
        ][0]
        if current_slot.seen_at is None:
            now = timezone.localtime(timezone.now())
            current_slot.seen_at = now
            current_slot.save(update_fields=["seen_at"])

        return self.current_slot_cursor

    def move_current_slot_cursor_back(self):
        if self.current_slot_cursor == 0:
            raise ValidationError("Cursor is in position 0")

        if self.event.exercises_shown_at_a_time is None:
            raise ValidationError("Event shows all exercises at once")

        self.current_slot_cursor = max(
            self.current_slot_cursor - self.event.exercises_shown_at_a_time, 0
        )
        self.save(update_fields=["current_slot_cursor"])
        return self.current_slot_cursor


class EventParticipationSlot(models.Model):
    """
    An EventParticipationSlot represents an exercise assigned to a participant to an
    event, the answer given by that student, and the assessment of a teacher.
    Slots can have children if the exercise assigned to a slot is an exercise that
    has children.
    """

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
    populating_rule = models.ForeignKey(
        EventTemplateRule,
        null=True,  # TODO make non-nullable when transition is complete
        blank=True,
        related_name="populated_slots",
        on_delete=models.PROTECT,
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
            ),
            models.UniqueConstraint(
                fields=["participation_id", "slot_number"],
                condition=Q(parent_id=None),
                name="event_participation_unique_base_slot_number",
            ),
        ]

    def __str__(self):
        return str(self.participation) + " " + str(self.slot_number)

    @property
    def has_answer(self):
        """
        Returns True iff the slot has been given an answer
        What an answer is, and thus the condition checked, depends
        on the type of the exercise associated to this slot
        """
        e_type = self.exercise.exercise_type
        if e_type in [
            Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
        ]:
            return self.selected_choices.exists()

        if e_type in [Exercise.OPEN_ANSWER, Exercise.JS, Exercise.C, Exercise.PYTHON]:
            return self.answer_text is not None and len(self.answer_text) > 0

        if e_type == Exercise.ATTACHMENT:
            return bool(self.attachment)

        if e_type in [Exercise.COMPLETION, Exercise.AGGREGATED]:
            return any(s.has_answer for s in self.sub_slots.all())

        assert False, "Type " + str(self.exercise.exercise_type) + " not implemented"

    @staticmethod
    def sanitize_json(json_data):
        json_data = json.dumps(json_data)
        json_data = json_data.replace("\\u0000", " ")
        return json.loads(json_data)

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
        pre_save_pk = self.pk
        super().save(*args, **kwargs)

        # run on transaction commit because, for multiple choice exercises,
        # it'll check whether a selected choice exists (i.e. a record in the
        # m2m table exists), but the record won't be visible yet because
        # this method is executed while still inside a transaction
        def update_answered_at_if_answer_exists():
            if self.has_answer:
                now = timezone.localtime(timezone.now())
                self.answered_at = now
                self.save(update_fields=["answered_at"])
                # update answered time of parent too
                if self.parent is not None and self.parent.answered_at is None:
                    self.parent.answered_at = now
                    self.parent.save(update_fields=["answered_at"])

        if self.answered_at is None and pre_save_pk is not None:
            transaction.on_commit(update_answered_at_if_answer_exists)

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
