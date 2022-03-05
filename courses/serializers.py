from django.db.models import Exists, OuterRef
from rest_framework import serializers
from users.serializers import UserSerializer

from courses.logic.privileges import MANAGE_EVENTS, check_privilege, get_user_privileges
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
from courses.serializer_fields import ReadWriteSerializerMethodField, RecursiveField


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
            "hidden",
        ]
        read_only_fields = ["creator"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.pop("preview", False):
            self.fields["participations"] = serializers.SerializerMethodField()
            self.fields[
                "unstarted_practice_events"
            ] = serializers.SerializerMethodField()

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
            context={"preview": True, **self.context},
        ).data

    def get_unstarted_practice_events(self, obj):
        """
        Returns Events with type SELF_SERVICE_PRACTICE created by the user
        for which a participation doesn't exist yet
        """
        try:
            user = self.context["request"].user
        except KeyError:
            return None

        # sub-query that retrieves a user's participation to events
        exists_user_participation = EventParticipation.objects.filter(
            user=user, event_instance__event=OuterRef("pk")
        )

        practice_events = Event.objects.annotate(
            user_participation_exists=Exists(exists_user_participation)
        ).filter(
            creator=user,
            course=obj,
            event_type=Event.SELF_SERVICE_PRACTICE,
            user_participation_exists=False,
        )

        return EventSerializer(practice_events, many=True, context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class CourseRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRole
        fields = ["id", "name", "allow_privileges"]


class ExerciseChoiceSerializer(HiddenFieldsModelSerializer):
    _ordering = serializers.IntegerField(required=False)

    class Meta:
        model = ExerciseChoice
        fields = ["id", "text", "_ordering"]
        hidden_fields = ["score"]


class ExerciseTestCaseSerializer(HiddenFieldsModelSerializer):
    _ordering = serializers.IntegerField(required=False)

    class Meta:
        model = ExerciseTestCase
        fields = ["id", "code", "text", "_ordering"]
        hidden_fields = ["testcase_type"]


class ExerciseSerializer(HiddenFieldsModelSerializer):
    public_tags = TagSerializer(many=True, required=False)
    private_tags = TagSerializer(
        many=True, required=False
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
            "max_score",
        ]
        hidden_fields = ["solution", "state"]

    def __init__(self, *args, **kwargs):
        kwargs.pop("required", None)  # TODO remove this
        super().__init__(*args, **kwargs)
        # TODO you might only show this to teachers (students will always only see exercises through slots)
        self.fields["sub_exercises"] = RecursiveField(many=True, required=False)

        kwargs.pop(
            "many", False
        )  # list serializer would pass this down to choice serializer, having parameter twice
        if self.context.pop("show_choices", True):
            self.fields["choices"] = ExerciseChoiceSerializer(
                many=True,
                required=False,
                *args,
                **kwargs,
            )

        if self.context.pop("show_testcases", True):
            self.fields["testcases"] = ExerciseTestCaseSerializer(
                many=True,
                required=False,
                *args,
                **kwargs,
            )

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


class EventTemplateRuleClauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTemplateRuleClause
        fields = ["id", "tags"]


class EventTemplateRuleSerializer(serializers.ModelSerializer):
    clauses = EventTemplateRuleClauseSerializer(many=True, read_only=True)
    _ordering = serializers.IntegerField(required=False)
    satisfying = serializers.SerializerMethodField()

    class Meta:
        model = EventTemplateRule
        fields = [
            "id",
            "rule_type",
            "exercises",
            "clauses",
            "amount",
            "_ordering",
            "satisfying",
        ]

    def get_satisfying(self, obj):
        qs = Exercise.objects.filter(course=obj.template.event.course).satisfying(obj)

        return {
            "count": qs.count(),
            "example": ExerciseSerializer(qs.first()).data if qs.count() > 0 else None,
        }


class EventTemplateSerializer(serializers.ModelSerializer):
    rules = EventTemplateRuleSerializer(many=True, read_only=True)

    class Meta:
        model = EventTemplate
        fields = ["id", "name", "rules"]
        read_only_fields = ["rules"]


class EventSerializer(HiddenFieldsModelSerializer):
    template = EventTemplateSerializer(read_only=True)
    participation_exists = serializers.SerializerMethodField()
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

    def get_state(self, obj):
        state = obj.state
        user = self.context["request"].user
        if (
            not check_privilege(user, obj.course, MANAGE_EVENTS)
            and state == Event.RESTRICTED
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

    score = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()

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
            "score",
            "comment",
            "execution_results",
        ]
        hidden_fields = [
            "seen_at",
            "answered_at",
        ]
        read_only_fields = ["execution_results"]

    def get_score(self, obj):
        if not obj.participation.is_assessment_available():
            return None

        return obj.assessment.score
        # return serializers.DecimalField(
        #     max_digits=5, decimal_places=2, source="assessment.score"
        # )

    def get_comment(self, obj):
        if not obj.participation.is_assessment_available():
            return None

        return obj.assessment.comment
        # return serializers.CharField(source="assessment.comment")


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
            # "execution_results"
        ]

        # read_only_fields = ['execution_results']

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
        self.fields["execution_results"] = serializers.JSONField(
            source="submission.execution_results", read_only=True
        )


class StudentViewEventParticipationSerializer(serializers.ModelSerializer):
    """
    Serializer used to show the slots of a participation's EventInstance to students
    during their participation to an event

    The slots include the fields necessary to submit answers to the exercises in
    those slots
    """

    event = serializers.SerializerMethodField()  # to pass context to EventSerializer
    score = serializers.SerializerMethodField()
    max_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        source="event_instance.max_score",
    )

    class Meta:
        model = EventParticipation
        fields = [
            "id",
            "state",
            "event",
            "last_slot_number",
            "begin_timestamp",
            "end_timestamp",
            "score",
            "max_score",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.pop("preview", False):
            self.fields["slots"] = ParticipationSubmissionSlotSerializer(
                many=True,
                source="submission.current_slots",
            )
        self.fields["assessment_available"] = serializers.SerializerMethodField()

    def get_assessment_available(self, obj):
        return obj.is_assessment_available()

    def get_score(self, obj):
        if not obj.is_assessment_available():
            return None

        return obj.assessment.score

    def get_event(self, obj):
        return EventSerializer(obj.event, read_only=True, context=self.context).data


class TeacherViewEventParticipationSerializer(serializers.ModelSerializer):
    """
    Serializer used to show the slots of a participation's EventInstance to teacher
    when assessing a participation to an event

    The slots include the fields necessary to see the answers given to an exercise and
    assign a score
    """

    event = serializers.SerializerMethodField()  # to pass context to EventSerializer
    slots = ParticipationAssessmentSlotSerializer(many=True, source="assessment.slots")
    user = UserSerializer(read_only=True)
    score = serializers.DecimalField(
        max_digits=5, decimal_places=2, source="assessment.score"
    )

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
            "event",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assessment_progress"] = serializers.IntegerField(
            source="assessment.assessment_progress", read_only=True
        )
        self.fields["visibility"] = serializers.IntegerField(
            source="assessment_visibility"
        )

    def get_event(self, obj):
        return EventSerializer(obj.event, read_only=True, context=self.context).data


class EventParticipationSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipationSubmissionSlot
        fields = [
            "id",
            "slot_number",
            "exercise",
            "sub_slots",
        ]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            capabilities = self.context.get("capabilities", {})

            if capabilities.get("assessment_fields_read", False):
                assessment_fields_write = capabilities.get(
                    "assessment_fields_write", False
                )
                self.fields["score"] = serializers.DecimalField(
                    max_digits=5,
                    decimal_places=2,
                    read_only=(not assessment_fields_write),
                )
                self.fields["comment"] = serializers.CharField(
                    read_only=(not assessment_fields_write),
                )

                self.fields["seen_at"] = serializers.DateTimeField(
                    source="submission.seen_at",
                    read_only=True,
                )
                self.fields["answered_at"] = serializers.DateTimeField(
                    source="submission.answered_at",
                    read_only=True,
                )

            if capabilities.get("submission_fields_read", False):
                submission_fields_write = capabilities.get(
                    "submission_fields_write", False
                )
                # TODO find a way to make these writable
                self.fields["selected_choices"] = serializers.PrimaryKeyRelatedField(
                    many=True,
                    source="submission.selected_choices",
                    read_only=(not submission_fields_write),
                )
                self.fields["attachment"] = serializers.FileField(
                    source="submission.attachment",
                    read_only=(not submission_fields_write),
                )
                self.fields["answer_text"] = serializers.CharField(
                    source="submission.answer_text",
                    read_only=(not submission_fields_write),
                )


class EventParticipationSerializer(serializers.ModelSerializer):
    max_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        source="event_instance.max_score",
    )

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
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        capabilities = self.context.get("capabilities", {})

        if capabilities.get("assessment_fields_read", False):
            # include teacher fields
            assessment_fields_write = capabilities.get("assessment_fields_write", False)
            # TODO currently cannot write to this field, refactor to have score as a property on participation
            self.fields["score"] = serializers.DecimalField(
                max_digits=5,
                decimal_places=2,
                source="assessment.score",
                read_only=(not assessment_fields_write),
            )
            self.fields["assessment_progress"] = serializers.IntegerField(
                source="assessment.assessment_progress",
            )
            self.fields["visibility"] = serializers.IntegerField(
                source="assessment_visibility",
                read_only=(not assessment_fields_write),
            )

        if capabilities.get("submission_fields_read", False):  # student fields
            self.fields["assessment_available"] = serializers.SerializerMethodField()

            if not hasattr(self.fields, "score"):  # don't re-define score field
                # add score as a read-only property and only if assessment has been published
                self.fields["score"] = serializers.SerializerMethodField()

    def get_assessment_available(self, obj):
        return obj.is_assessment_available()

    def get_score(self, obj):
        if not obj.is_assessment_available():
            return None

        return obj.assessment.score


class EventInstanceSlotSerializer(serializers.ModelSerializer):
    pass


class EventInstanceSerializer(serializers.ModelSerializer):
    pass
