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


class RecursiveField(serializers.Serializer):
    """
    Used for serializers that contain self-referencing fields
    """

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


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


class ParticipationAssessmentSlotSerializer(serializers.ModelSerializer):
    pass


class ParticipationAssessmentSerializer(serializers.ModelSerializer):
    pass


class ParticipationSubmissionSlotSerializer(serializers.ModelSerializer):
    pass


class ParticipationSubmissionSerializer(serializers.ModelSerializer):
    pass


class EventParticipationSlotSerializer(serializers.ModelSerializer):
    sub_slots = RecursiveField(many=True)
    selected_choice = ExerciseChoiceSerializer()
    score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        source="assessment.score",
    )

    class Meta:
        model = ParticipationSubmissionSlot
        fields = [
            "slot_number",
            "exercise",
            "sub_slots",
            "score",
            "selected_choice",
            "answer_text",
            "attachment",
            "seen_at",
            "answered_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exercise"] = ExerciseSerializer(context={"show_choices": False})


class EventParticipationSerializer(serializers.ModelSerializer):
    slots = EventParticipationSlotSerializer(many=True, source="submission.slots")

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "slots",
        ]
