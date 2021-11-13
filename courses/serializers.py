from rest_framework import serializers

from courses.models import (
    Course,
    Event,
    EventInstanceSlot,
    EventParticipation,
    Exercise,
    ExerciseChoice,
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


class ExerciseSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = Exercise
        fields = ["id", "text", "exercise_type", "tags"]
        hidden_fields = ["solution", "state"]


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = ExerciseChoice
        fields = ["text"]
        hidden_fields = ["correct"]


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
    exercise = ExerciseSerializer()
    sub_slots = RecursiveField(many=True)

    class Meta:
        model = EventInstanceSlot
        fields = [
            "slot_number",
            "exercise",
            "sub_slots",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["score"] = serializers.SerializerMethodField()
        # TODO submission fields and other assessment fields

    def get_score(self, obj):
        return obj.get_assessment(self.context["participation"]).score


class EventParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slots"] = serializers.SerializerMethodField()

    def get_slots(self, obj):
        return EventParticipationSlotSerializer(
            obj.event_instance.slots.all(),
            many=True,
            context={
                "participation": obj
            },  # ? is there a way to access obj inside of __init__ instead?
        ).data
