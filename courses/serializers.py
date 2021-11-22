from rest_framework import serializers

from courses.models import (
    Course,
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
)
from courses.serializer_fields import RecursiveField


class HiddenFieldsModelSerializer(serializers.ModelSerializer):
    """
    Used to conditionally show certain fields only when the `context` argument
    is provided and contains key `show_hidden_fields` with a truthy value
    """

    def __init__(self, *args, **kwargs):
        context = kwargs.get("context", None)
        if context is not None and context.get("show_hidden_fields", False):
            self.Meta.fields.extend(self.Meta.hidden_fields)
        super().__init__(*args, **kwargs)

        # for easier use by other serializers that rely on this property after __init__
        self.show_hidden_fields = self.context.get("show_hidden_fields", False)


class CourseSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "description", "creator"]
        read_only_fields = ["creator"]
        hidden_fields = ["visible", "teachers"]


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = ExerciseChoice
        fields = ["id", "text"]
        hidden_fields = ["score"]


class ExerciseSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "text",
            "exercise_type",
            "label",
            # "child_position",
            # "tags",
        ]
        hidden_fields = ["solution", "state"]

    def __init__(self, *args, **kwargs):
        kwargs.pop("required", None)  # TODO remove this
        super().__init__(*args, **kwargs)
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


class EventSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "instructions",
            "begin_timestamp",
            "end_timestamp",
            "event_type",
            "progression_rule",
            "state",
        ]
        hidden_fields = ["template"]


class EventTemplateRuleClauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTemplateRuleClause
        fields = ["tags"]


class EventTemplateRuleSerializer(serializers.ModelSerializer):
    clauses = EventTemplateRuleClauseSerializer(many=True)

    class Meta:
        model = EventTemplateRule
        fields = ["rule_type", "target_slot_number", "exercises", "clauses"]


class EventTemplateSerializer(serializers.ModelSerializer):
    rules = EventTemplateRuleSerializer(many=True)

    class Meta:
        model = EventTemplate
        fields = ["name", "rules"]


class ParticipationSubmissionSlotSerializer(serializers.ModelSerializer):
    sub_slots = RecursiveField(many=True)
    exercise = ExerciseSerializer()

    class Meta:
        model = ParticipationSubmissionSlot
        fields = [
            "id",
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


class EventInstanceSlotSerializer(serializers.ModelSerializer):
    pass


class EventInstanceSerializer(serializers.ModelSerializer):
    pass
