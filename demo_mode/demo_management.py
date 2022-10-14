from courses.logic.presentation import (
    EVENT_SHOW_HIDDEN_FIELDS,
    EXERCISE_SHOW_HIDDEN_FIELDS,
)
from django.http import HttpRequest

from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventParticipationSlot,
    EventTemplateRule,
    EventTemplateRuleClause,
    Exercise,
    ExerciseSolution,
)
from courses.serializers import EventSerializer, ExerciseSerializer
from django.db import transaction

DEMO_COURSES = [
    ("Analisi Matematica", ""),
    ("Laboratorio JavaScript", ""),
    ("Fondamenti di programmazione C", ""),
]
import string
import random


def get_random_string(length=7):
    letters = [*string.ascii_letters, *string.digits]
    return "".join(random.choice(letters) for _ in range(length))


def get_blueprint_courses():
    return Course.objects.filter(creator_id=1)


def create_demo_courses_for(user):
    blueprint_courses = get_blueprint_courses()

    def get_context():
        context = {}
        request = HttpRequest()
        request.user = user
        context["request"] = request
        return context

    with transaction.atomic():
        for (name, description) in DEMO_COURSES:
            blueprint_course = blueprint_courses.get(name=name)
            new_course = Course.objects.create(
                name=name + " (" + get_random_string() + ")",
                description=description,
                creator=user,
            )

            print("CREATED", new_course.pk, new_course.name)

            # clone exercises
            for exercise in blueprint_course.exercises.all():
                serializer = ExerciseSerializer(
                    data=ExerciseSerializer(  # deep clone exercise
                        exercise, context={EXERCISE_SHOW_HIDDEN_FIELDS: True}
                    ).data,
                    context={EXERCISE_SHOW_HIDDEN_FIELDS: True, **get_context()},
                )
                serializer.is_valid()
                new_exercise = serializer.save(
                    course_id=new_course.pk, state=Exercise.PUBLIC
                )
                for solution in exercise.solutions.all():
                    ExerciseSolution.objects.create(
                        exercise=new_exercise,
                        content=solution.content,
                        state=solution.state,
                        user=solution.user,
                    )

            # clone events
            for event in blueprint_course.events.filter(event_type=Event.EXAM):
                serializer = EventSerializer(
                    data=EventSerializer(  # deep clone exam
                        event, context={EVENT_SHOW_HIDDEN_FIELDS: True, **get_context()}
                    ).data,
                    context={EVENT_SHOW_HIDDEN_FIELDS: True},
                )
                serializer.is_valid()
                new_event = serializer.save(course_id=new_course.pk, state=event.state)

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
