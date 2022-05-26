from django.db.models import Exists, OuterRef
from rest_framework import serializers
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
    """
    Used to conditionally show certain fields only when the `context` argument
    is provided and contains key `show_hidden_fields` with a truthy value
    """

    # note: using this serializer the way shown below has proven to be incorrect, as the methods
    # init and get_field_names may be called only once and affect all future accesses to the serializer
    # for now, the best thing seems to be checking the context manually in each serializer.
    # try and find another abstraction for this behavior (maybe even generalizable, such as having a dict of
    # {string: string[]ƒ}, where the key of a record if a property that must be in the context in order to have
    # the fields in the value included)

    pass

    # def __init__(self, *args, **kwargs):
    #     print("____________________-INITING______________________")
    #     context = kwargs.get("context")
    #     self.show_hidden_fields = context is not None and context.get(
    #         "show_hidden_fields", False
    #     )

    #     if self.show_hidden_fields:
    #         print("????????????SHOWING HIDDEN FIELDS???????????")
    #         # self.Meta.fields.extend(self.Meta.hidden_fields)
    #     super().__init__(*args, **kwargs)

    # def get_field_names(self, declared_fields, info):
    #     show_hidden_fields = self.context is not None and self.context.get(
    #         "show_hidden_fields", False
    #     )
    #     self.show_hidden_fields = False
    #     fields = super().get_field_names(declared_fields, info)
    #     if show_hidden_fields:
    #         fields.extend(self.Meta.hidden_fields)
    #     print("fields:", fields)
    #     return fields


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
            # "is_enrolled",
            "privileges",
            "hidden",
        ]
        read_only_fields = ["creator"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.pop("preview", False):
            self.fields["participations"] = serializers.SerializerMethodField()
            self.fields[
                "unstarted_practice_events"
            ] = serializers.SerializerMethodField()
            self.fields["public_exercises_exist"] = serializers.SerializerMethodField()

    def get_privileges(self, obj):
        return get_user_privileges(self.context["request"].user, obj)

    def get_public_exercises_exist(self, obj):
        return obj.exercises.public().exists()

    def get_participations(self, obj):
        try:
            user = self.context["request"].user
        except KeyError:
            return None

        participations = (
            EventParticipation.objects.all()
            .with_prefetched_base_slots()
            .filter(user=user, event__course=obj)
        )
        return EventParticipationSerializer(
            participations,
            many=True,
            context={
                # "include_slots": False,
                "capabilities": {
                    "assessment_fields_read": True,
                    "submission_fields_read": True,
                },
                **self.context,
            },
        ).data

    def get_unstarted_practice_events(self, obj):
        """
        Returns Events with type SELF_SERVICE_PRACTICE created by the user
        for which a participation doesn't exist yet
        """
        try:
            user = self.context["request"].user
        except KeyError:
            return None

        # sub-query that retrieves a user's participation to events
        exists_user_participation = (
            EventParticipation.objects.all()
            .with_prefetched_base_slots()
            .filter(user=user, event=OuterRef("pk"))
        )

        practice_events = Event.objects.annotate(
            user_participation_exists=Exists(exists_user_participation)
        ).filter(
            creator=user,
            course=obj,
            event_type=Event.SELF_SERVICE_PRACTICE,
            user_participation_exists=False,
        )

        return EventSerializer(practice_events, many=True, context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("show_exercise_count", False):
            self.fields["public_exercises"] = serializers.SerializerMethodField()

    def get_public_exercises(self, obj):
        return obj.public_in_exercises.filter(state=Exercise.PUBLIC).count()


class CourseRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRole
        fields = ["id", "name", "allow_privileges"]


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    _ordering = serializers.IntegerField(required=False)

    class Meta:
        model = ExerciseChoice
        fields = ["id", "text", "_ordering"]
        # hidden_fields = ["score"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get(
            "show_solution",
            False,
        ) or self.context.get("show_hidden_fields", False):
            self.fields["score_selected"] = serializers.DecimalField(
                max_digits=5, decimal_places=1
            )
            self.fields["score_unselected"] = serializers.DecimalField(
                max_digits=5, decimal_places=1
            )


class ExerciseTestCaseSerializer(HiddenFieldsModelSerializer):
    _ordering = serializers.IntegerField(required=False)

    class Meta:
        model = ExerciseTestCase
        fields = ["id", "code", "text", "_ordering", "stdin", "expected_stdout"]
        # hidden_fields = ["testcase_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("show_hidden_fields", False):
            self.fields["testcase_type"] = serializers.IntegerField()
        else:
            # for unauthorized users, overwrite code and text fields to enforce visibility rule
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


class ExerciseSerializer(HiddenFieldsModelSerializer):
    public_tags = TagSerializer(many=True, required=False)
    text = serializers.CharField(trim_whitespace=False, allow_blank=True)

    class Meta:
        model = Exercise
        fields = [
            "id",
            "text",
            "exercise_type",
            "label",
            "public_tags",
            "max_score",
            "initial_code",
            "state",
            "requires_typescript",
        ]
        # hidden_fields = ["solution", "state"]

    def __init__(self, *args, **kwargs):
        kwargs.pop("required", None)  # TODO remove this
        super().__init__(*args, **kwargs)
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
                context=self.context,
                # *args,
                # **kwargs,
            )
        if self.context.pop("show_testcases", True):
            self.fields["testcases"] = ExerciseTestCaseSerializer(
                many=True,
                required=False,
                context=self.context,
                # *args,
                # **kwargs,
            )

        if self.context.get("show_hidden_fields", False):
            self.fields["locked_by"] = UserSerializer(read_only=True)
            self.fields["private_tags"] = TagSerializer(many=True, required=False)
        else:  # TODO find a more elegant way
            self.fields.pop("state", None)

        if self.context.get("show_hidden_fields", False) or self.context.get(
            "show_solution", False
        ):
            self.fields["solution"] = serializers.CharField(
                required=False, allow_blank=True
            )
            self.fields["correct_choices"] = serializers.SerializerMethodField()

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


class EventTemplateRuleSerializer(serializers.ModelSerializer):
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

    def get_satisfying(self, obj):
        qs = Exercise.objects.filter(course=obj.template.event.course).satisfying(obj)

        return {
            "count": qs.count(),
            "example": ExerciseSerializer(
                qs.first(), context={"show_hidden_fields": True}
            ).data
            if qs.count() > 0
            else None,
        }


class EventTemplateSerializer(serializers.ModelSerializer):
    rules = EventTemplateRuleSerializer(many=True, read_only=True)

    class Meta:
        model = EventTemplate
        fields = ["id", "name", "rules"]
        read_only_fields = ["rules"]


class EventSerializer(HiddenFieldsModelSerializer):
    id = HashidSerializerCharField(source_field="courses.Event.id", read_only=True)
    template = serializers.SerializerMethodField()
    participation_exists = serializers.SerializerMethodField()
    state = ReadWriteSerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "instructions",
            "begin_timestamp",
            "end_timestamp",
            "event_type",
            "state",
            "allow_going_back",
            "exercises_shown_at_a_time",
            "template",
            "users_allowed_past_closure",
            "participation_exists",  # ! TODO don't always show
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("show_hidden_fields", False):
            self.fields["locked_by"] = UserSerializer(read_only=True)
            self.fields["users_allowed_past_closure"] = serializers.ManyRelatedField(
                child_relation=serializers.PrimaryKeyRelatedField(
                    queryset=User.objects.all(), required=False
                ),
                required=False,
            )
            self.fields["randomize_rule_order"] = serializers.BooleanField()
            self.fields["access_rule"] = serializers.IntegerField(
                allow_null=True,
                required=False,
            )
            self.fields["access_rule_exceptions"] = serializers.JSONField(
                allow_null=True,
                required=False,
            )

    def get_state(self, obj):
        state = obj.state
        user = self.context["request"].user
        if (
            not check_privilege(user, obj.course, MANAGE_EVENTS)
            and state == Event.RESTRICTED
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
        if (
            self.context.get("show_hidden_fields", False)
            or obj.event_type == Event.SELF_SERVICE_PRACTICE
        ):
            return EventTemplateSerializer(obj.template).data
        return None


class EventParticipationSlotSerializer(serializers.ModelSerializer):
    exercise = serializers.SerializerMethodField()  # to pass context
    # sub_slots = RecursiveField(
    #     many=True, read_only=True
    # )
    # serializers.SerializerMethodField()  # to pass context
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
            "is_last",
            "is_first",
        ]
        read_only_fields = ["id", "seen_at", "answered_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        if capabilities.get("submission_fields_read", False,) and not self.context.get(
            "preview",
            False,
        ):
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
        return (
            ExerciseSerializer(obj.exercise, context=self.context).data
            if not self.context.get("preview", False)
            else None
        )

    def get_answer_text(self, obj):
        """
        Does some processing on the answer text value
        """
        # TODO put this in separate module
        text = obj.answer_text
        text = re.sub(r'src="([^"]+)"', "", text)
        text = re.sub(r"</?p( style=('|\")[^\"']*('|\"))?>", "", text)
        return text


class EventParticipationSerializer(serializers.ModelSerializer):
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
            "score",
            "max_score",
            "event",
            "last_slot_number",
            "current_slot_cursor",
            "bookmarked",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        return (
            EventSerializer(obj.event, read_only=True, context=self.context).data
            if not self.context.get("preview", False)
            else None
        )

    def get_slots(self, obj):
        if self.context.get("capabilities").get("assessment_fields_read", False):
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
