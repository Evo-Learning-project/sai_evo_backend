from rest_framework import serializers

from courses.models import (
    Course,
    Event,
    EventInstanceSlot,
    EventParticipation,
    Exercise,
    ExerciseChoice,
    ParticipationAssessmentSlot,
    ParticipationSubmissionSlot,
)
from courses.serializer_fields import (
    NestedSerializerForeignKeyWritableField,
    RecursiveField,
)


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
        hidden_fields = ["visible", "teachers"]


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = ExerciseChoice
        fields = ["text"]
        hidden_fields = ["score"]


class ExerciseSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "text",
            "exercise_type",
            "tags",
        ]
        hidden_fields = ["solution", "state"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.pop("show_choices", True):
            self.fields["choices"] = ExerciseChoiceSerializer(
                many=True,
                *args,
                **kwargs,
            )


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


class EventTemplateRuleSerializer(serializers.ModelSerializer):
    pass


class EventTemplateSerializer(serializers.ModelSerializer):
    pass


class EventInstanceSlotSerializer(serializers.ModelSerializer):
    pass


class EventInstanceSerializer(serializers.ModelSerializer):
    pass


class ParticipationSubmissionSlotSerializer(serializers.ModelSerializer):
    sub_slots = RecursiveField(many=True)
    exercise = ExerciseSerializer()

    class Meta:
        model = ParticipationSubmissionSlot
        fields = [
            "id",
            "exercise",
            "sub_slots",
            "selected_choice",
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
        self.fields["selected_choice"] = ExerciseChoiceSerializer(
            source="submission.selected_choice", read_only=True
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

    slots = ParticipationSubmissionSlotSerializer(many=True, source="submission.slots")

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "slots",
        ]


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
