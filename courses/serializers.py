from rest_framework import serializers

from courses.models import (
    Course,
    Event,
    EventInstanceSlot,
    EventParticipation,
    Exercise,
    ExerciseChoice,
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


class EventParticipationSlotSerializer(HiddenFieldsModelSerializer):
    sub_slots = RecursiveField(many=True)
    selected_choice = NestedSerializerForeignKeyWritableField(
        serializer=ExerciseChoiceSerializer,
        queryset=ExerciseChoice.objects.all(),
    )

    class Meta:
        model = ParticipationSubmissionSlot
        fields = [
            "slot_number",
            "exercise",
            "sub_slots",
            "selected_choice",
            "answer_text",
            "attachment",
        ]
        read_only_fields = [  # TODO make sure these aren't changed
            "slot_number",
            "exercise",
            "seen_at",
            "answered_at",
        ]
        hidden_fields = [
            "seen_at",
            "answered_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.show_hidden_fields:
            self.fields["score"] = serializers.DecimalField(
                max_digits=5,
                decimal_places=2,
                source="assessment.score",
            )
        self.fields["exercise"] = ExerciseSerializer(read_only=True)


class EventParticipationSerializer(serializers.ModelSerializer):
    slots = EventParticipationSlotSerializer(many=True, source="submission.slots")

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "slots",
        ]


class ParticipationAssessmentSlotSerializer(serializers.ModelSerializer):
    pass


class ParticipationAssessmentSerializer(serializers.ModelSerializer):
    pass


class ParticipationSubmissionSlotSerializer(serializers.ModelSerializer):
    pass


class ParticipationSubmissionSerializer(serializers.ModelSerializer):
    pass
