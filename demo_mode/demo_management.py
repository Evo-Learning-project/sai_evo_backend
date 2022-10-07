from courses.logic.presentation import (
    EVENT_SHOW_HIDDEN_FIELDS,
    EXERCISE_SHOW_HIDDEN_FIELDS,
)
from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventParticipationSlot,
    EventTemplateRule,
    EventTemplateRuleClause,
    Exercise,
)
from courses.serializers import EventSerializer, ExerciseSerializer


DEMO_COURSES = [
    ("Analisi Matematica", ""),
    # ("Programmazione JavaScript", ""),
    # ("Programmazione C"),
]


def get_blueprint_courses():
    return Course.objects.filter(creator_id=1)


def create_demo_courses_for(user):
    blueprint_courses = get_blueprint_courses()
    for (name, description) in DEMO_COURSES:
        blueprint_course = blueprint_courses.get(name=name)
        new_course = Course.objects.create(
            name=name, description=description, creator=user
        )

        # clone exercises
        for exercise in blueprint_course.exercises.all():
            serializer = ExerciseSerializer(
                data=ExerciseSerializer(  # deep clone exercise
                    exercise, context={EXERCISE_SHOW_HIDDEN_FIELDS: True}
                ).data,
                context={EXERCISE_SHOW_HIDDEN_FIELDS: True},
            )
            serializer.is_valid()
            serializer.save(course_id=new_course.pk, state=Exercise.PUBLIC)

        # clone events
        for event in blueprint_course.events.filter(event_type=Event.EXAM):
            serializer = EventSerializer(
                data=EventSerializer(  # deep clone exam
                    event, context={EVENT_SHOW_HIDDEN_FIELDS: True}
                ).data,
                context={EVENT_SHOW_HIDDEN_FIELDS: True},
            )
            serializer.is_valid()
            new_event = serializer.save(course_id=new_course.pk, state=Exercise.PUBLIC)

            # clone template rules
            template = new_event.template
            for rule in template.rules.all():
                new_rule = EventTemplateRule.objects.create(
                    template_id=template.pk, rule_type=rule.rule_type
                )
                new_rule.exercises.set(rule.exercises.all())
                # clone template rule tags
                for clause in rule.clauses.all():
                    new_clause = EventTemplateRuleClause.objects.create(
                        rule_id=new_rule.pk
                    )
                    new_clause.tags.set(clause.tags.all())

            # clone event participation
            for participation in event.participations.all():
                # manually instantiate model to prevent triggering manager
                new_participation = EventParticipation(
                    user=participation.user, event=new_event
                )
                new_participation.save()
                # clone slots
                slot_number = 0
                for slot in participation.slots.all().base_slots():
                    new_slot = EventParticipationSlot.objects.create(
                        participation=new_participation,
                        slot_number=slot_number,
                        exercise=slot.exercise,
                        answer_text=slot.answer_text,
                    )
                    new_slot.selected_choices.set(slot.selected_choices.all())
                    slot_number += 1
