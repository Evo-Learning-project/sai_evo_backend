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
    ParticipationAssessment,
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
    # is_enrolled = serializers.SerializerMethodField()
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
        ]
        read_only_fields = ["creator"]
        hidden_fields = ["visible"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.pop("preview", False):
            self.fields["participations"] = serializers.SerializerMethodField()

    # def get_is_enrolled(self, obj):
    #     return self.context["request"].user in obj.enrolled_users.all()

    def get_privileges(self, obj):
        return get_user_privileges(self.context["request"].user, obj)

    def get_participations(self, obj):
        try:
            user = self.context["request"].user
        except KeyError:
            return None

        participations = EventParticipation.objects.filter(
            user=user, event_instance__event__course=obj
        )
        return StudentViewEventParticipationSerializer(
            participations,
            many=True,
            context={"preview": True},
        ).data


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
    public_tags = TagSerializer(many=True, read_only=True)
    private_tags = TagSerializer(
        many=True, read_only=True
    )  # TODO hide from non-teachers

    class Meta:
        model = Exercise
        fields = [
            "id",
            "text",
            "exercise_type",
            "label",
            # "child_position",
            "public_tags",
            "private_tags",
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
        fields = ["id", "tags"]


class EventTemplateRuleSerializer(serializers.ModelSerializer):
    clauses = EventTemplateRuleClauseSerializer(many=True, read_only=True)
    target_slot_number = serializers.IntegerField(source="_ordering", read_only=True)

    class Meta:
        model = EventTemplateRule
        fields = [
            "id",
            "rule_type",
            "target_slot_number",
            "exercises",
            "clauses",
        ]

    # read_only_fields = ["target_slot_number"]


class EventTemplateSerializer(serializers.ModelSerializer):
    rules = EventTemplateRuleSerializer(many=True, read_only=True)

    class Meta:
        model = EventTemplate
        fields = ["id", "name", "rules"]
        read_only_fields = ["rules"]


class EventSerializer(HiddenFieldsModelSerializer):
    template = EventTemplateSerializer(read_only=True)
    state = serializers.IntegerField()
    participation_exists = serializers.SerializerMethodField()

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
            "participation_exists",
        ]
        hidden_fields = [
            # TODO make hidden fields work
            # "template",
            # "users_allowed_past_closure",
            "exercises_shown_at_a_time",
            "access_rule",
            "access_rule_exceptions",
        ]

    def get_participation_exists(self, obj):
        try:
            user = self.context["request"].user
            return EventParticipation.objects.filter(
                user=user, event_instance__event=obj
            ).exists()
        except KeyError:
            return None


class ParticipationSubmissionSlotSerializer(serializers.ModelSerializer):
    sub_slots = RecursiveField(many=True)
    exercise = ExerciseSerializer()
    is_last = serializers.BooleanField(
        read_only=True,
        source="participation.is_cursor_last_position",
    )
    is_first = serializers.BooleanField(
        read_only=True,
        source="participation.is_cursor_first_position",
    )

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
            "is_last",
            "is_first",
        ]
        hidden_fields = [
            "seen_at",
            "answered_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.context.pop("show_assessment"):
            self.fields["score"] = serializers.DecimalField(
                max_digits=5, decimal_places=2, source="assessment.score"
            )
            self.fields["comment"] = serializers.CharField(source="assessment.comment")


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
            "assessment_state",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO remove the read_only
        self.fields["selected_choices"] = serializers.PrimaryKeyRelatedField(
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

    event = EventSerializer(read_only=True)

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "event",
            "last_slot_number",
            "begin_timestamp",
            "end_timestamp",
            # "slots",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.pop("preview", False):
            self.fields["slots"] = ParticipationSubmissionSlotSerializer(
                many=True,
                source="submission.current_slots",
                context={"show_assessment": self.context.pop("show_assessment", False)},
            )
        self.fields["assessment_available"] = serializers.SerializerMethodField()

    def get_assessment_available(self, obj):
        return obj.assessment.state == ParticipationAssessment.PUBLISHED


class TeacherViewEventParticipationSerializer(serializers.ModelSerializer):
    """
    Serializer used to show the slots of a participation's EventInstance to teacher
    when assessing a participation to an event

    The slots include the fields necessary to see the answers given to an exercise and
    assign a score
    """

    slots = ParticipationAssessmentSlotSerializer(many=True, source="assessment.slots")
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
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assessment_progress"] = serializers.IntegerField(
            source="assessment.assessment_progress", read_only=True
        )
        self.fields["visibility"] = serializers.IntegerField(
            source="assessment_visibility"
        )


class EventInstanceSlotSerializer(serializers.ModelSerializer):
    pass


class EventInstanceSerializer(serializers.ModelSerializer):
    pass
