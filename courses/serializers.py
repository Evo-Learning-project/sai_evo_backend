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
        hidden_fields = ["solution", "draft"]
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
        hidden_fields = ["limit_access_to", "template"]
