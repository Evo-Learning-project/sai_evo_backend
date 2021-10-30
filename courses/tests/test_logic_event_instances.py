from courses.models import Course, Event, EventTemplate, EventTemplateRule, Exercise
from django.test import TestCase
from tags.models import Tag


class EventTemplateManagerTestCase(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="course")
        self.event = Event.objects.create(
            name="event", event_type=Event.EXAM, course=self.course
        )
        self.tag1 = Tag.objects.create(name="tag1", course=self.course)
        self.tag2 = Tag.objects.create(name="tag2", course=self.course)
        self.tag3 = Tag.objects.create(name="tag3", course=self.course)
        self.tag4 = Tag.objects.create(name="tag4", course=self.course)
        self.tag5 = Tag.objects.create(name="tag5", course=self.course)
        self.tag6 = Tag.objects.create(name="tag6", course=self.course)
        self.tag7 = Tag.objects.create(name="tag7", course=self.course)
        self.tag8 = Tag.objects.create(name="tag8", course=self.course)
        self.tag9 = Tag.objects.create(name="tag9", course=self.course)
        self.e1 = Exercise.objects.create(
            text="a",
            course=self.course,
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            choices=[{"text": "aa", "correct": True}],
        )
        self.e2 = Exercise.objects.create(
            text="b",
            course=self.course,
            exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            choices=[
                {"text": "aa", "correct": True},
                {"text": "aa", "correct": False},
            ],
        )
        self.e3 = Exercise.objects.create(
            text="c",
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )
        self.e4 = Exercise.objects.create(
            text="c",
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )
        self.e5 = Exercise.objects.create(
            text="c",
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )
        self.e6 = Exercise.objects.create(
            text="c",
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )
        self.e7 = Exercise.objects.create(
            text="c",
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )

        for i in range(0, 100):
            Exercise.objects.create(
                text="dummy exercises " + str(i),
                exercise_type=Exercise.OPEN_ANSWER,
                course=self.course,
            )

        rules = [
            {
                "rule_type": EventTemplateRule.ID_BASED,
                "exercises": [self.e1, self.e2],
            },
            {
                "rule_type": EventTemplateRule.TAG_BASED,
                "tags": [
                    [self.tag1, self.tag2],
                ],
            },
            {
                "rule_type": EventTemplateRule.TAG_BASED,
                "tags": [
                    [self.tag7],
                    [self.tag2, self.tag3, self.tag4],
                    [self.tag5, self.tag6],
                ],
            },
            {
                "rule_type": EventTemplateRule.TAG_BASED,
                "tags": [[self.tag9], [self.tag8]],
            },
        ]

        self.template = EventTemplate.objects.create(course=self.course, rules=rules)

        self.e1.tags.set([self.tag1, self.tag3])  # eligible for rule 1 and rule 2
        self.e2.tags.set([self.tag1, self.tag2])  # eligible for rule 1, rule 2
        self.e3.tags.set(
            [self.tag7, self.tag4, self.tag5, self.tag6]
        )  # eligible for rule 3
        self.e4.tags.set(
            [self.tag7, self.tag4, self.tag5, self.tag8]  # eligible for rule 3
        )
        self.e5.tags.set(
            [
                self.tag7,
                self.tag4,
                self.tag6,
                self.tag1,
            ]  # eligible for rule 2 and rule 3
        )
        self.e6.tags.set([self.tag9, self.tag8])  # eligible for rule 4

    def test_get_exercises_from_template(self):
        # shows the function get_exercises_from(template) correctly applies the rules
        # of the supplied template to retrieve exercises
        from courses.logic.event_instances import get_exercises_from

        for _ in range(0, 100):
            exercises = get_exercises_from(self.template)
            self.assertIn(exercises[0].pk, [self.e1.pk, self.e2.pk])
            self.assertIn(
                exercises[1].pk, [self.e1.pk, self.e2.pk, self.e5.pk, self.e6.pk]
            )
            self.assertIn(exercises[2].pk, [self.e3.pk, self.e4.pk, self.e5.pk])
            self.assertIn(exercises[3].pk, [self.e6.pk])
