from rest_framework import serializers

from courses.models import Course, Event, Exercise, ExerciseChoice


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
        fields = ["name", "description", "creator"]
        hidden_fields = ["visible", "teachers"]


class ExerciseSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = Exercise
        fields = ["text", "exercise_type", "tags"]
        hidden_fields = ["solution", "state"]
        # type_specific_fields = {
        #     Exercise.AGGREGATED: "sub_exercises",
        #     Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE: "choices",
        # }


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = ExerciseChoice
        fields = ["text"]
        hidden_fields = ["correct"]


class EventSerializer(HiddenFieldsModelSerializer):
    class Meta:
        model = Event
        fields = [
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
    # use EventInstanceSlot as model and have fields from ParticipationAssessmentSlotSerializer
    # and ParticipationSubmissionSlotSerializer; this is meant as a read only serializer
    pass


class EventParticipationSerializer(serializers.ModelSerializer):
    pass
