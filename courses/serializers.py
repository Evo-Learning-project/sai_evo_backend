from rest_framework import serializers
from users.serializers import UserSerializer

from courses.logic.privileges import get_user_privileges
from courses.models import (
    Course,
    CourseRole,
    Event,
    EventInstanceSlot,
    EventParticipation,
    EventTemplate,
    EventTemplateRule,
    EventTemplateRuleClause,
    Exercise,
    ExerciseChoice,
    ExerciseTestCase,
    ParticipationAssessmentSlot,
    ParticipationSubmissionSlot,
    Tag,
)
from courses.serializer_fields import RecursiveField


class HiddenFieldsModelSerializer(serializers.ModelSerializer):
    """
    Used to conditionally show certain fields only when the `context` argument
    is provided and contains key `show_hidden_fields` with a truthy value
    """

    def __init__(self, *args, **kwargs):
        context = kwargs.get("context")
        self.show_hidden_fields = context is not None and context.get(
            "show_hidden_fields", False
        )

        if self.show_hidden_fields:
            self.Meta.fields.extend(self.Meta.hidden_fields)
        super().__init__(*args, **kwargs)


class CourseSerializer(HiddenFieldsModelSerializer):
    is_enrolled = serializers.SerializerMethodField()
    privileges = serializers.SerializerMethodField()
    creator = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "creator",
            "is_enrolled",
            "privileges",
        ]
        read_only_fields = ["creator"]
        hidden_fields = ["visible"]

    def get_is_enrolled(self, obj):
        return self.context["request"].user in obj.enrolled_users.all()

    def get_privileges(self, obj):
        return get_user_privileges(self.context["request"].user, obj)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class CourseRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRole
        fields = ["id", "name", "allow_privileges"]


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = ExerciseChoice
        fields = ["id", "text"]
        hidden_fields = ["score"]


class ExerciseSerializer(HiddenFieldsModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            "id",
            "text",
            "exercise_type",
            "label",
            # "child_position",
            "tags",
        ]
        hidden_fields = ["solution", "state"]

    def __init__(self, *args, **kwargs):
        kwargs.pop("required", None)  # TODO remove this
        super().__init__(*args, **kwargs)
        # TODO you might only show this to teachers (students will always only see exercises through slots)
        self.fields["sub_exercises"] = RecursiveField(many=True, required=False)

        if self.context.pop("show_choices", True):
            self.fields["choices"] = ExerciseChoiceSerializer(
                many=True,
                required=False,
                *args,
                **kwargs,
            )

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        # print(validated_data)
        return Exercise.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # ignore related objects , as they must be dealt
        # with individually with their own entry points
        validated_data.pop("choices", [])
        validated_data.pop("testcases", [])
        validated_data.pop("sub_exercises", [])

        return super().update(instance, validated_data)


class EventTemplateRuleClauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTemplateRuleClause
        fields = ["tags"]


class EventTemplateRuleSerializer(serializers.ModelSerializer):
    clauses = EventTemplateRuleClauseSerializer(many=True, read_only=True)

    class Meta:
        model = EventTemplateRule
        fields = ["id", "rule_type", "target_slot_number", "exercises", "clauses"]
        read_only_fields = ["target_slot_number"]


class EventTemplateSerializer(serializers.ModelSerializer):
    rules = EventTemplateRuleSerializer(many=True, read_only=True)

    class Meta:
        model = EventTemplate
        fields = ["id", "name", "rules"]
        read_only_fields = ["rules"]


class EventSerializer(HiddenFieldsModelSerializer):
    template = EventTemplateSerializer(read_only=True)

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
        ]
        hidden_fields = [
            # "template",
            "users_allowed_past_closure",
            "exercises_shown_at_a_time",
            "access_rule",
            "access_rule_exceptions",
        ]


class ParticipationSubmissionSlotSerializer(serializers.ModelSerializer):
    sub_slots = RecursiveField(many=True)
    exercise = ExerciseSerializer()

    class Meta:
        model = ParticipationSubmissionSlot
        fields = [
            "id",
            "slot_number",
            "exercise",
            "sub_slots",
            "selected_choices",
            "answer_text",
            "attachment",
        ]
        hidden_fields = [
            "seen_at",
            "answered_at",
        ]


class ParticipationAssessmentSlotSerializer(serializers.ModelSerializer):
    sub_slots = RecursiveField(many=True, read_only=True)
    exercise = ExerciseSerializer(read_only=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = ParticipationAssessmentSlot
        fields = [
            "id",
            "slot_number",
            "exercise",
            "score",
            "comment",
            "sub_slots",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO remove the read_only
        self.fields["selected_choices"] = ExerciseChoiceSerializer(
            many=True, source="submission.selected_choices", read_only=True
        )
        self.fields["attachment"] = serializers.FileField(
            source="submission.attachment", read_only=True
        )
        self.fields["answer_text"] = serializers.CharField(
            source="submission.answer_text", read_only=True
        )
        self.fields["seen_at"] = serializers.DateTimeField(
            source="submission.seen_at", read_only=True
        )
        self.fields["answered_at"] = serializers.DateTimeField(
            source="submission.answered_at", read_only=True
        )


class StudentViewEventParticipationSerializer(serializers.ModelSerializer):
    """
    Serializer used to show the slots of a participation's EventInstance to students
    during their participation to an event

    The slots include the fields necessary to submit answers to the exercises in
    those slots
    """

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "slots",
        ]

    def __init__(self, *args, **kwargs):
        self.fields["slots"] = ParticipationSubmissionSlotSerializer(
            many=True, source="submission.current_slots"
        )


class TeacherViewEventParticipationSerializer(serializers.ModelSerializer):
    """
    Serializer used to show the slots of a participation's EventInstance to teacher
    when assessing a participation to an event

    The slots include the fields necessary to see the answers given to an exercise and
    assign a score
    """

    slots = ParticipationAssessmentSlotSerializer(many=True, source="assessment.slots")

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "slots",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assessment_progress"] = serializers.IntegerField(
            source="assessment.assessment_progress", read_only=True
        )


class EventInstanceSlotSerializer(serializers.ModelSerializer):
    pass


class EventInstanceSerializer(serializers.ModelSerializer):
    pass
