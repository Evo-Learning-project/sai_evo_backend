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
    pass


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

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if not self.context.pop(
    #         "preview", False
    #     ):  # TODO make inside_student_dashboard condition explicit
    #         # meant to be shown inside student dashboard
    #         self.add_student_dashboard_fields()

    # def add_student_dashboard_fields(self):
    #     # self.fields["participations"] = serializers.SerializerMethodField()
    #     self.fields["unstarted_practice_events"] = serializers.SerializerMethodField()
    #     self.fields["public_exercises_count"] = serializers.SerializerMethodField()

    def get_privileges(self, obj):
        return get_user_privileges(self.context["request"].user, obj)

    def get_public_exercises_count(self, obj):
        return obj.exercises.public().count()

    # def get_participations(self, obj):
    #     try:
    #         user = self.context["request"].user
    #     except KeyError:
    #         return None

    #     participations = (
    #         EventParticipation.objects.all()
    #         .with_prefetched_base_slots()
    #         .filter(user=user, event__course=obj)
    #         .select_related("user", "event")
    #     )
    #     return EventParticipationSerializer(
    #         participations,
    #         many=True,
    #         context={
    #             "capabilities": {
    #                 "assessment_fields_read": True,
    #                 "submission_fields_read": True,
    #             },
    #             "preview": True,
    #             **self.context,
    #         },
    #     ).data

    # def get_unstarted_practice_events(self, obj):
    #     """
    #     Returns Events with type SELF_SERVICE_PRACTICE created by the user
    #     for which a participation doesn't exist yet
    #     """
    #     try:
    #         user = self.context["request"].user
    #     except KeyError:
    #         return None

    #     # sub-query that retrieves a user's participation to events
    #     exists_user_participation = (
    #         EventParticipation.objects.all()
    #         .with_prefetched_base_slots()
    #         .filter(user=user, event=OuterRef("pk"))
    #     )

    #     practice_events = Event.objects.annotate(
    #         user_participation_exists=Exists(exists_user_participation)
    #     ).filter(
    #         creator=user,
    #         course=obj,
    #         event_type=Event.SELF_SERVICE_PRACTICE,
    #         user_participation_exists=False,
    #     )

    #     return EventSerializer(practice_events, many=True, context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("show_exercise_count", False):  # TODO
            self.add_public_exercise_count_fields()

    def add_public_exercise_count_fields(self):
        self.fields["public_exercises"] = serializers.SerializerMethodField()
        self.fields["public_exercises_not_seen"] = serializers.SerializerMethodField()

    def get_public_exercises(self, obj):
        return len(obj.prefetched_public_in_public_exercises)

    def get_public_exercises_not_seen(self, obj):
        return len(obj.prefetched_public_in_unseen_public_exercises)


class CourseRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRole
        fields = ["id", "name", "allow_privileges"]


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    _ordering = serializers.IntegerField(required=False)

    class Meta:
        model = ExerciseChoice
        fields = ["id", "text", "_ordering"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get(
            "show_solution",
            False,
        ) or self.context.get("show_hidden_fields", False):
            # to be used when a teacher accesses the object or the solution
            # to an exam/practice is being shown
            self.add_score_fields()

    def add_score_fields(self):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("show_hidden_fields", False):
            self.fields["testcase_type"] = serializers.IntegerField()
        else:
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
            )
        if self.context.pop("show_testcases", True):
            self.fields["testcases"] = ExerciseTestCaseSerializer(
                many=True,
                required=False,
                context=self.context,
            )

        if self.context.get(
            "show_hidden_fields", False
        ):  # TODO make condition explicit
            # meant to be shown only to teachers
            self.add_hidden_fields()
        else:  # TODO find a more elegant way
            self.fields.pop("state", None)

        if self.context.get("show_hidden_fields", False) or self.context.get(
            "show_solution", False
        ):
            self.add_solution_fields()

    def add_hidden_fields(self):
        self.fields["locked_by"] = UserSerializer(read_only=True)
        self.fields["private_tags"] = TagSerializer(many=True, required=False)

    def add_solution_fields(self):
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

    class Meta:
        model = EventTemplateRule
        fields = [
            "id",
            "rule_type",
            "exercises",
            "clauses",
            "amount",
            "_ordering",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get(
            "show_hidden_fields", False
        ):  # TODO make condition explicit
            # meant to be shown to teachers when using a tag-based rule
            self.fields["satisfying"] = serializers.SerializerMethodField()

    def get_satisfying(self, obj):
        qs = Exercise.objects.filter(course=obj.template.event.course).satisfying(obj)

        return {
            "count": qs.count(),
            "example": ExerciseSerializer(
                qs.first(), context={"show_hidden_fields": True}  # TODO make explicit
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


class EventSerializer(HiddenFieldsModelSerializer):
    id = HashidSerializerCharField(source_field="courses.Event.id", read_only=True)
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
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get(
            "show_hidden_fields", False
        ):  # TODO make condition explicit
            # meant to be shown to teachers only
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

        if not self.context.get("preview", False):
            # TODO separate these two fields: participation_exists should only be shown when accessing the event in detail mode, template when???
            self.fields["template"] = serializers.SerializerMethodField()
            self.fields["participation_exists"] = serializers.SerializerMethodField()

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
                self.context.get("show_hidden_fields", False)  # TODO make explicit
                or obj.event_type == Event.SELF_SERVICE_PRACTICE
            )
            else None
        )


class EventParticipationSlotSerializer(serializers.ModelSerializer):
    exercise = serializers.SerializerMethodField()  # to pass context

    class Meta:
        model = EventParticipationSlot
        fields = [
            "id",
            "slot_number",
            "exercise",
            "sub_slots",
            "seen_at",
            "answered_at",
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

        if not self.context.get("preview", False):
            self.fields["is_last"] = serializers.BooleanField(
                read_only=True,
                source="participation.is_cursor_last_position",
            )
            self.fields["is_first"] = serializers.BooleanField(
                read_only=True,
                source="participation.is_cursor_first_position",
            )

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
        return EventSerializer(obj.event, read_only=True, context=self.context).data

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
