from django.db.models import Exists, OuterRef
from rest_framework import serializers
from courses.logic.presentation import (
    CHOICE_SHOW_SCORE_FIELDS,
    EVENT_PARTICIPATION_SHOW_SLOTS,
    EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS,
    EVENT_SHOW_HIDDEN_FIELDS,
    EVENT_SHOW_PARTICIPATION_EXISTS,
    EVENT_SHOW_TEMPLATE,
    EVENT_TEMPLATE_RULE_SHOW_SATISFYING_FIELD,
    EXERCISE_SHOW_HIDDEN_FIELDS,
    EXERCISE_SHOW_SOLUTION_FIELDS,
    TAG_SHOW_PUBLIC_EXERCISES_COUNT,
    TESTCASE_SHOW_HIDDEN_FIELDS,
)
from users.models import User
from users.serializers import UserSerializer
from hashid_field.rest import HashidSerializerCharField

from courses.logic.privileges import MANAGE_EVENTS, check_privilege, get_user_privileges
from courses.models import (
    Course,
    CourseRole,
    Event,
    EventParticipation,
    EventParticipationSlot,
    EventTemplate,
    EventTemplateRule,
    EventTemplateRuleClause,
    Exercise,
    ExerciseChoice,
    ExerciseTestCase,
    Tag,
)
from courses.serializer_fields import (
    FileWithPreviewField,
    ReadWriteSerializerMethodField,
    RecursiveField,
)
import re


class HiddenFieldsModelSerializer(serializers.ModelSerializer):
    pass


class ConditionalFieldsMixin:
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.remove_unsatisfied_condition_fields()

    def remove_unsatisfied_condition_fields(self):
        conditional_fields = self.Meta.conditional_fields

        for condition, fields in conditional_fields.items():
            if not self.context.get(condition, False):
                for field in fields:
                    self.fields.pop(field)


class CourseSerializer(serializers.ModelSerializer):
    privileges = serializers.SerializerMethodField()
    creator = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "creator",
            "privileges",
            "hidden",
        ]
        read_only_fields = ["creator"]

    def get_privileges(self, obj):
        return get_user_privileges(self.context["request"].user, obj)

    def get_public_exercises_count(self, obj):
        return obj.exercises.public().count()


class TagSerializer(serializers.ModelSerializer, ConditionalFieldsMixin):
    public_exercises = serializers.SerializerMethodField()
    public_exercises_not_seen = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ["id", "name", "public_exercises", "public_exercises_not_seen"]

        conditional_fields = {
            TAG_SHOW_PUBLIC_EXERCISES_COUNT: [
                "public_exercises",
                "public_exercises_not_seen",
            ]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_unsatisfied_condition_fields()

    def get_public_exercises(self, obj):
        return len(obj.prefetched_public_in_public_exercises)

    def get_public_exercises_not_seen(self, obj):
        return len(obj.prefetched_public_in_unseen_public_exercises)


class CourseRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRole
        fields = ["id", "name", "allow_privileges"]


class ExerciseChoiceSerializer(serializers.ModelSerializer, ConditionalFieldsMixin):
    _ordering = serializers.IntegerField(required=False)

    class Meta:
        model = ExerciseChoice
        fields = ["id", "text", "_ordering", "score_selected", "score_unselected"]

        conditional_fields = {
            EXERCISE_SHOW_SOLUTION_FIELDS: ["score_selected", "score_unselected"]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_unsatisfied_condition_fields()


class ExerciseTestCaseSerializer(serializers.ModelSerializer, ConditionalFieldsMixin):
    _ordering = serializers.IntegerField(required=False)

    class Meta:
        model = ExerciseTestCase
        fields = [
            "id",
            "code",
            "text",
            "_ordering",
            "stdin",
            "expected_stdout",
            "testcase_type",
        ]

        conditional_fields = {
            TESTCASE_SHOW_HIDDEN_FIELDS: ["testcase_type", "code", "text"]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_unsatisfied_condition_fields()

        self.TESTCASE_SHOW_HIDDEN_FIELDS = self.context.get(
            TESTCASE_SHOW_HIDDEN_FIELDS, False
        )
        if not self.TESTCASE_SHOW_HIDDEN_FIELDS:
            # for unauthorized users, overwrite code and text
            # fields to enforce visibility rule
            self.add_relevant_public_info_fields()

    def add_relevant_public_info_fields(self):
        self.fields["code"] = serializers.SerializerMethodField()
        self.fields["text"] = serializers.SerializerMethodField()

    def get_code(self, obj):
        return (
            obj.code
            if obj.testcase_type == ExerciseTestCase.SHOW_CODE_SHOW_TEXT
            else None
        )

    def get_text(self, obj):
        return (
            obj.text
            if obj.testcase_type == ExerciseTestCase.SHOW_CODE_SHOW_TEXT
            or obj.testcase_type == ExerciseTestCase.SHOW_TEXT_ONLY
            else None
        )


class ExerciseSerializer(serializers.ModelSerializer, ConditionalFieldsMixin):
    public_tags = TagSerializer(many=True, required=False)
    private_tags = TagSerializer(many=True, required=False)
    text = serializers.CharField(trim_whitespace=False, allow_blank=True)
    correct_choices = serializers.SerializerMethodField()
    locked_by = UserSerializer(read_only=True)

    class Meta:
        model = Exercise
        fields = [
            "id",
            "text",
            "exercise_type",
            "label",
            "public_tags",
            "private_tags",
            "max_score",
            "initial_code",
            "state",
            "requires_typescript",
            "solution",
            "correct_choices",
            "locked_by",
        ]

        conditional_fields = {
            EXERCISE_SHOW_SOLUTION_FIELDS: ["solution", "correct_choices"],
            EXERCISE_SHOW_HIDDEN_FIELDS: [
                "locked_by",
                "private_tags",
                "state",
                "label",
            ],
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("required", None)  # TODO remove this
        super().__init__(*args, **kwargs)

        self.remove_unsatisfied_condition_fields()

        # TODO you might only show this to teachers (students will always only see exercises through slots)
        self.fields["sub_exercises"] = RecursiveField(
            many=True,
            required=False,
            context=self.context,
        )

        # list serializer would pass this down to choice serializer, having parameter twice
        kwargs.pop("many", False)

        if self.context.pop("show_choices", True):
            self.fields["choices"] = ExerciseChoiceSerializer(
                many=True,
                required=False,
                context={
                    CHOICE_SHOW_SCORE_FIELDS: self.context.get(
                        EXERCISE_SHOW_SOLUTION_FIELDS
                    )
                },
            )
        if self.context.pop("show_testcases", True):
            self.fields["testcases"] = ExerciseTestCaseSerializer(
                many=True,
                required=False,
                context={
                    TESTCASE_SHOW_HIDDEN_FIELDS: self.context.get(
                        EXERCISE_SHOW_SOLUTION_FIELDS
                    )
                },
            )

    def create(self, validated_data):
        public_tags = validated_data.pop("public_tags", [])
        private_tags = validated_data.pop("private_tags", [])
        instance = Exercise.objects.create(**validated_data)

        for tag_name in public_tags:
            tag, _ = Tag.objects.get_or_create(
                course_id=validated_data["course_id"], name=tag_name["name"]
            )
            instance.public_tags.add(tag)

        for tag_name in private_tags:
            tag, _ = Tag.objects.get_or_create(
                course_id=validated_data["course_id"], name=tag_name["name"]
            )
            instance.private_tags.add(tag)

        return instance

    def update(self, instance, validated_data):
        # ignore related objects , as they must be dealt
        # with individually with their own entry points
        validated_data.pop("choices", [])
        validated_data.pop("testcases", [])
        validated_data.pop("sub_exercises", [])
        validated_data.pop("private_tags", [])
        validated_data.pop("public_tags", [])

        return super().update(instance, validated_data)

    def get_correct_choices(self, obj):
        # workaround for drf bug https://github.com/encode/django-rest-framework/issues/6084
        if isinstance(obj, Exercise):
            return [c.pk for c in obj.get_correct_choices()]

        return []


class EventTemplateRuleClauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTemplateRuleClause
        fields = ["id", "tags"]


class EventTemplateRuleSerializer(serializers.ModelSerializer, ConditionalFieldsMixin):
    clauses = EventTemplateRuleClauseSerializer(many=True, read_only=True)
    _ordering = serializers.IntegerField(required=False)
    satisfying = serializers.SerializerMethodField()

    class Meta:
        model = EventTemplateRule
        fields = [
            "id",
            "rule_type",
            "exercises",
            "clauses",
            "amount",
            "_ordering",
            "satisfying",
        ]

        conditional_fields = {
            # ? move to a separate api call
            EVENT_TEMPLATE_RULE_SHOW_SATISFYING_FIELD: ["satisfying"]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_unsatisfied_condition_fields()

    def get_satisfying(self, obj):
        qs = Exercise.objects.filter(course=obj.template.event.course).satisfying(obj)

        return {
            "count": qs.count(),
            "example": ExerciseSerializer(
                qs.first(), context={EXERCISE_SHOW_HIDDEN_FIELDS: True}
            ).data
            if qs.count() > 0
            else None,
        }


class EventTemplateSerializer(serializers.ModelSerializer):
    rules = serializers.SerializerMethodField()  # to pass context

    class Meta:
        model = EventTemplate
        fields = ["id", "name", "rules"]
        read_only_fields = ["rules"]

    def get_rules(self, obj):
        return EventTemplateRuleSerializer(
            obj.rules.all(), many=True, context=self.context
        ).data


class EventSerializer(serializers.ModelSerializer, ConditionalFieldsMixin):
    id = HashidSerializerCharField(source_field="courses.Event.id", read_only=True)
    state = ReadWriteSerializerMethodField()
    locked_by = UserSerializer(read_only=True)
    template = serializers.SerializerMethodField()
    participation_exists = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "instructions",
            "begin_timestamp",
            "end_timestamp",
            "event_type",
            "template",
            "state",
            "allow_going_back",
            "exercises_shown_at_a_time",
            "locked_by",
            "users_allowed_past_closure",
            "participation_exists",
            "randomize_rule_order",
            "access_rule",
            "access_rule_exceptions",
        ]

        conditional_fields = {
            EVENT_SHOW_HIDDEN_FIELDS: [
                "locked_by",
                "users_allowed_past_closure",
                "randomize_rule_order",
                "access_rule",
                "access_rule_exceptions",
            ],
            EVENT_SHOW_TEMPLATE: ["template"],
            EVENT_SHOW_PARTICIPATION_EXISTS: ["participation_exists"],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_unsatisfied_condition_fields()

    def get_state(self, obj):
        state = obj.state
        user = self.context["request"].user
        if state == Event.RESTRICTED and not check_privilege(
            user,
            obj.course,
            MANAGE_EVENTS,
        ):
            return (
                Event.OPEN
                if user in obj.users_allowed_past_closure.all()
                else Event.CLOSED
            )
        return state

    def get_participation_exists(self, obj):
        try:
            user = self.context["request"].user
            return obj.participations.filter(user=user).exists()
        except KeyError:
            return None

    def get_template(self, obj):
        return (
            EventTemplateSerializer(obj.template, context=self.context).data
            if (
                self.context.get(EVENT_SHOW_HIDDEN_FIELDS, False)
                or obj.event_type == Event.SELF_SERVICE_PRACTICE
            )
            else None
        )


class EventParticipationSlotSerializer(
    serializers.ModelSerializer, ConditionalFieldsMixin
):
    exercise = serializers.SerializerMethodField()  # to pass context
    is_last = serializers.BooleanField(
        read_only=True,
        source="participation.is_cursor_last_position",
    )
    is_first = serializers.BooleanField(
        read_only=True,
        source="participation.is_cursor_first_position",
    )

    class Meta:
        model = EventParticipationSlot
        fields = [
            "id",
            "slot_number",
            "exercise",
            "sub_slots",
            "seen_at",
            "answered_at",
            "is_first",
            "is_last",
        ]
        read_only_fields = ["id", "seen_at", "answered_at"]

        conditional_fields = {
            EVENT_PARTICIPATION_SLOT_SHOW_DETAIL_FIELDS: ["is_first", "is_last"]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_unsatisfied_condition_fields()

        capabilities = self.context.get("capabilities", {})

        self.fields["sub_slots"] = RecursiveField(
            many=True,
            read_only=True,
            context=self.context,
        )

        if capabilities.get("assessment_fields_read", False):
            assessment_fields_write = capabilities.get("assessment_fields_write", False)
            self.fields["score"] = serializers.DecimalField(
                max_digits=5,
                decimal_places=1,
                allow_null=True,
                read_only=(not assessment_fields_write),
            )
            self.fields["comment"] = serializers.CharField(
                read_only=(not assessment_fields_write), allow_blank=True
            )
            self.fields["score_edited"] = serializers.BooleanField(
                read_only=True,
            )

        if capabilities.get("submission_fields_read", False):
            submission_fields_write = capabilities.get("submission_fields_write", False)
            selected_choices_kwargs = {"read_only": (not submission_fields_write)}
            if not selected_choices_kwargs["read_only"]:
                selected_choices_kwargs["queryset"] = ExerciseChoice.objects.all()
            self.fields["selected_choices"] = serializers.PrimaryKeyRelatedField(
                many=True, **selected_choices_kwargs
            )
            self.fields["attachment"] = FileWithPreviewField(
                read_only=(not submission_fields_write),
            )
            if self.context.get("trim_images_in_text", False):
                self.fields["answer_text"] = serializers.SerializerMethodField()
            else:
                self.fields["answer_text"] = serializers.CharField(
                    read_only=(not submission_fields_write),
                    allow_blank=True,
                )
            self.fields["execution_results"] = serializers.JSONField(read_only=True)

    def get_exercise(self, obj):
        return ExerciseSerializer(obj.exercise, context=self.context).data

    def get_answer_text(self, obj):
        """
        Does some processing on the answer text value
        """
        # TODO put this in separate module
        text = obj.answer_text
        text = re.sub(r'src="([^"]+)"', "", text)
        text = re.sub(r"</?p( style=('|\")[^\"']*('|\"))?>", "", text)
        return text


class EventParticipationSerializer(serializers.ModelSerializer, ConditionalFieldsMixin):
    event = serializers.SerializerMethodField()  # to pass context
    slots = serializers.SerializerMethodField()  # to pass context
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "slots",
            "user",
            "begin_timestamp",
            "end_timestamp",
            "max_score",
            "event",
            "last_slot_number",
            "current_slot_cursor",
            "bookmarked",
        ]

        conditional_fields = {EVENT_PARTICIPATION_SHOW_SLOTS: ["slots"]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_unsatisfied_condition_fields()

        capabilities = self.context.get("capabilities", {})

        if capabilities.get("assessment_fields_read", False):
            # include teacher fields
            assessment_fields_write = capabilities.get("assessment_fields_write", False)
            self.fields["score"] = serializers.CharField(
                allow_null=True,
                read_only=(not assessment_fields_write),
            )
            self.fields["score_edited"] = serializers.BooleanField(
                read_only=True,
            )
            self.fields["assessment_progress"] = serializers.IntegerField(
                read_only=True
            )
            self.fields["visibility"] = serializers.IntegerField(
                source="assessment_visibility",
                read_only=(not assessment_fields_write),
            )

        if capabilities.get("submission_fields_read", False):  # student fields
            self.fields["assessment_available"] = serializers.BooleanField(
                source="is_assessment_available", read_only=True
            )

    def get_event(self, obj):
        return EventSerializer(obj.event, read_only=True, context=self.context).data

    def get_slots(self, obj):
        if self.context.get("capabilities").get("assessment_fields_read", False):
            # accessing outside of active participation - show all slots
            slots = obj.prefetched_base_slots
        else:
            slots = obj.current_slots

        ret = (
            EventParticipationSlotSerializer(
                slots,
                many=True,
                context=self.context,
            ).data
            if self.context.get("include_slots", True)
            else None
        )
        return ret
