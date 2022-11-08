from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventTemplate,
    EventTemplateRule,
    EventTemplateRuleClause,
    Exercise,
    Tag,
)
from django.core.exceptions import ValidationError
from django.test import TestCase
from users.models import User


class ExerciseManagerTestCase(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="test_course")
        self.e1_text = "aaa"

    def test_multiple_choice_single_possible_exercise_creation(self):
        # supplying choices together with the exercise data creates the choices
        # related to that exercise
        choices = [
            {
                "text": "c1",
            },
            {
                "text": "c2",
            },
            {
                "text": "c3",
            },
        ]

        e1 = Exercise.objects.create(
            text=self.e1_text,
            choices=choices,
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            course=self.course,
        )

        self.assertEqual(e1.text, self.e1_text)
        self.assertEqual(e1.exercise_type, Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE)
        self.assertEqual(  # related choices were created
            e1.choices.count(),
            len(choices),
        )
        self.assertListEqual(
            [
                {
                    "text": c.text,
                }
                for c in e1.choices.all()
            ],
            choices,
        )

        # creating a multiple choice question with test cases fails
        with self.assertRaises(ValidationError):
            Exercise.objects.create(
                text="bbb",
                testcases=[{"code": "aaa"}, {"code": "ccc"}],
                exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                course=self.course,
            )

    def test_multiple_choice_multiple_possible_exercise_creation(self):
        choices = [
            {
                "text": "c1",
            },
            {
                "text": "c2",
            },
            {
                "text": "c3",
            },
        ]

        e1 = Exercise.objects.create(
            text=self.e1_text,
            choices=choices,
            exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            course=self.course,
        )

        self.assertEqual(e1.text, self.e1_text)
        self.assertEqual(e1.exercise_type, Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE)

        self.assertEqual(e1.choices.count(), len(choices))

        i = 0
        for choice in e1.choices.all():
            # the created choices are the same ones supplied for the parent exercise
            self.assertEqual({"text": choice.text}, choices[i])
            i += 1

        # creating a multiple choice question with test cases fails
        with self.assertRaises(ValidationError):
            Exercise.objects.create(
                text="bbb",
                testcases=[{"code": "aaa"}, {"code": "ccc"}],
                exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
                course=self.course,
            )

    def test_open_answer_exercise_creation(self):
        e1 = Exercise.objects.create(
            text=self.e1_text,
            exercise_type=Exercise.OPEN_ANSWER,
            course=self.course,
        )

        self.assertEqual(e1.text, self.e1_text)
        self.assertEqual(e1.exercise_type, Exercise.OPEN_ANSWER)

        # creating an open question with test cases fails
        with self.assertRaises(ValidationError):
            Exercise.objects.create(
                text="bbb",
                testcases=[{"code": "aaa"}, {"code": "ccc"}],
                exercise_type=Exercise.OPEN_ANSWER,
                course=self.course,
            )

        # creating an open question with choices fails
        with self.assertRaises(ValidationError):
            Exercise.objects.create(
                text="bbb",
                choices=[
                    {
                        "text": "c1",
                    }
                ],
                exercise_type=Exercise.OPEN_ANSWER,
                course=self.course,
            )

    def test_completion_exercise_creation(self):
        choices = [  # choices are supplied as a list of lists
            [
                {
                    "text": "1c1",
                },
                {
                    "text": "1c2",
                },
            ],
            [
                {
                    "text": "2c1",
                },
                {
                    "text": "2c2",
                },
            ],
            [
                {
                    "text": "3c1",
                },
                {
                    "text": "3c2",
                },
                {
                    "text": "3c3",
                },
            ],
        ]

        sub_exercises = [
            {
                "text": "",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                "choices": choices[0],
            },
            {
                "text": "",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                "choices": choices[1],
            },
            {
                "text": "",
                "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                "choices": choices[2],
            },
        ]

        e1 = Exercise.objects.create(
            text=self.e1_text,
            sub_exercises=sub_exercises,
            exercise_type=Exercise.COMPLETION,
            course=self.course,
        )

        self.assertEqual(  # a sub-exercise is created for each group of choices supplied
            e1.sub_exercises.count(),
            3,
        )

        i = 0
        for sub_exercise in e1.sub_exercises.all():
            self.assertEqual(sub_exercise.text, "")  # sub-exercises have empty text

            self.assertListEqual(  # the supplied choices are assigned to the sub-exercises
                [
                    {
                        "text": c.text,
                    }
                    for c in sub_exercise.choices.all()
                ],
                choices[i],
            )
            i += 1

    def test_aggregated_exercise_creation(self):
        sub_e1 = {
            "text": "sub1",
            "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            "choices": [
                {
                    "text": "1c1",
                },
                {
                    "text": "1c2",
                },
            ],
        }
        sub_e2 = {
            "text": "sub2",
            "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            "choices": [
                {
                    "text": "2c1",
                },
                {
                    "text": "2c2",
                },
            ],
        }

        sub_e3 = {
            "text": "sub3",
            "exercise_type": Exercise.OPEN_ANSWER,
        }

        sub_exercises = [sub_e1, sub_e2, sub_e3]

        e1 = Exercise.objects.create(
            text=self.e1_text,
            exercise_type=Exercise.AGGREGATED,
            course=self.course,
            sub_exercises=sub_exercises,
        )

        self.assertEqual(  # sub-exercises have been created
            e1.sub_exercises.count(),
            len(sub_exercises),
        )

        # show that a sub-exercise cannot be assigned to a parent from another course
        sub_1 = e1.sub_exercises.first()
        another_course = Course.objects.create(name="another")
        another_exercise = Exercise.objects.create(
            course=another_course, text="", exercise_type=Exercise.OPEN_ANSWER
        )
        with self.assertRaises(ValidationError):
            sub_1.parent = another_exercise
            sub_1.save()

        i = 0
        for sub_exercise in e1.sub_exercises.all():
            self.assertDictEqual(
                {
                    "text": sub_exercise.text,
                    "exercise_type": sub_exercise.exercise_type,
                },
                {
                    "text": sub_exercises[i]["text"],
                    "exercise_type": sub_exercises[i]["exercise_type"],
                },
            )
            i += 1

    def test_js_exercise_creation(self):
        testcases = [
            {"code": "abc"},
            {"code": "def"},
            {"code": "ghi"},
        ]

        e1 = Exercise.objects.create(
            text=self.e1_text,
            course=self.course,
            exercise_type=Exercise.JS,
            testcases=testcases,
        )
        self.assertEqual(e1.text, self.e1_text)
        self.assertEqual(e1.exercise_type, Exercise.JS)
        self.assertEqual(
            e1.testcases.count(),
            len(testcases),
        )
        self.assertListEqual(
            [{"code": t.code} for t in e1.testcases.all()],
            testcases,
        )

        # creating a JS exercise with choices fails
        with self.assertRaises(ValidationError):
            Exercise.objects.create(
                text="bbb",
                choices=[
                    {
                        "text": "aaa",
                    },
                    {
                        "text": "ccc",
                    },
                ],
                exercise_type=Exercise.JS,
                course=self.course,
            )

    def test_attachment_exercise_creation(self):
        e1 = Exercise.objects.create(
            text=self.e1_text,
            exercise_type=Exercise.ATTACHMENT,
            course=self.course,
        )

        self.assertEqual(e1.text, self.e1_text)
        self.assertEqual(e1.exercise_type, Exercise.ATTACHMENT)

        # creating an attachment exercise with test cases fails
        with self.assertRaises(ValidationError):
            Exercise.objects.create(
                text="bbb",
                testcases=[{"code": "aaa"}, {"code": "ccc"}],
                exercise_type=Exercise.ATTACHMENT,
                course=self.course,
            )

        # creating an attachment exercise with choices fails
        with self.assertRaises(ValidationError):
            Exercise.objects.create(
                text="bbb",
                choices=[
                    {
                        "text": "c1",
                    }
                ],
                exercise_type=Exercise.ATTACHMENT,
                course=self.course,
            )

    def test_base_exercises_queryset(self):
        e1 = Exercise.objects.create(
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            course=self.course,
        )
        e2 = Exercise.objects.create(
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            course=self.course,
            parent=e1,
        )
        e3 = Exercise.objects.create(
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            course=self.course,
            parent=e1,
        )
        e4 = Exercise.objects.create(
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            course=self.course,
        )
        e5 = Exercise.objects.create(
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            course=self.course,
            parent=e2,
        )

        self.assertIn(e1, Exercise.objects.base_exercises())
        self.assertIn(e4, Exercise.objects.base_exercises())
        self.assertNotIn(e2, Exercise.objects.base_exercises())
        self.assertNotIn(e3, Exercise.objects.base_exercises())
        self.assertNotIn(e5, Exercise.objects.base_exercises())


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
        self.e1 = Exercise.objects.create(
            text="a",
            course=self.course,
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            choices=[
                {
                    "text": "aa",
                }
            ],
        )
        self.e2 = Exercise.objects.create(
            text="b",
            course=self.course,
            exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            choices=[
                {
                    "text": "aa",
                },
                {
                    "text": "aa",
                },
            ],
        )
        self.e3 = Exercise.objects.create(
            text="c",
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )

    def test_event_template_creation(self):
        # show that the manager creates an EventTemplate and its related EventTemplateRules
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
                    [self.tag1],
                    [self.tag2, self.tag3, self.tag4],
                    [self.tag5, self.tag6],
                    [self.tag7, self.tag8],
                ],
            },
        ]

        template = EventTemplate.objects.create(course=self.course)  # rules=rules)
        for rule in rules:
            exercises = rule.pop("exercises", [])
            tags = rule.pop("tags", [])
            r = EventTemplateRule.objects.create(**rule, template=template)
            r.exercises.set(exercises)
            for tag_group in tags:
                c = EventTemplateRuleClause.objects.create(rule=r)
                c.tags.set(tag_group)
            rule["exercises"] = exercises
            rule["tags"] = tags

        i = 0
        for rule in template.rules.all():
            self.assertEqual(rule.rule_type, rules[i]["rule_type"])
            if rule.rule_type == EventTemplateRule.ID_BASED:
                self.assertSetEqual(
                    set([e.pk for e in rule.exercises.all()]),
                    set([e.pk for e in rules[i]["exercises"]]),
                )
            else:
                # show that a clause has been created for each group of tags supplied
                self.assertEqual(rule.clauses.count(), len(rules[i]["tags"]))
                j = 0
                for clause in rule.clauses.all():
                    self.assertListEqual(
                        [t.pk for t in clause.tags.all()],
                        [t.pk for t in rules[i]["tags"][j]],
                    )
                    j += 1
            i += 1


class EventParticipationManagerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="aaa@bbb.com", username="a")
        self.course = Course.objects.create(name="course")
        self.other_course = Course.objects.create(name="course2")
        self.event = Event.objects.create(
            name="event", event_type=Event.EXAM, course=self.course
        )
        self.event_other_course = Event.objects.create(
            name="event", event_type=Event.EXAM, course=self.other_course
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
            state=Exercise.PRIVATE,
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            choices=[
                {
                    "text": "aa",
                }
            ],
        )
        self.e1_other_course = Exercise.objects.create(
            text="a",
            course=self.other_course,
            state=Exercise.PRIVATE,
            exercise_type=Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            choices=[
                {
                    "text": "aa",
                }
            ],
        )
        self.e2 = Exercise.objects.create(
            text="b",
            state=Exercise.PRIVATE,
            course=self.course,
            exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            choices=[
                {
                    "text": "aa",
                },
                {
                    "text": "aa",
                },
            ],
        )
        self.e3 = Exercise.objects.create(
            text="c",
            state=Exercise.PRIVATE,
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )
        self.e4 = Exercise.objects.create(
            text="d",
            state=Exercise.PRIVATE,
            course=self.course,
            exercise_type=Exercise.AGGREGATED,
            sub_exercises=[
                {
                    "text": "aaa",
                    "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
                    "choices": [
                        {
                            "text": "a",
                        },
                        {
                            "text": "b",
                        },
                    ],
                },
                {
                    "text": "bbb",
                    "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
                    "choices": [
                        {
                            "text": "a",
                        },
                        {
                            "text": "b",
                        },
                    ],
                },
            ],
        )
        self.e5 = Exercise.objects.create(
            text="e",
            state=Exercise.PRIVATE,
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )
        self.e6 = Exercise.objects.create(
            text="f",
            state=Exercise.PRIVATE,
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )
        self.e7 = Exercise.objects.create(
            text="g",
            state=Exercise.PRIVATE,
            course=self.course,
            exercise_type=Exercise.OPEN_ANSWER,
        )

        for i in range(0, 20):
            Exercise.objects.create(
                text="dummy exercises " + str(i),
                exercise_type=Exercise.OPEN_ANSWER,
                course=self.course,
                state=Exercise.PRIVATE,
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

        for rule in rules:
            EventTemplateRule.objects.create(template=self.event.template, **rule)

        # dummy rule from another course to test validation
        self.rule_template_other_course = EventTemplateRule.objects.create(
            template=self.event_other_course.template,
            rule_type=EventTemplateRule.ID_BASED,
        )
        self.rule_template_other_course.exercises.set([self.e1_other_course])

        self.template = self.event.template

        self.e1.public_tags.set([self.tag1, self.tag3])  # satisfies rule 1 and rule 2
        self.e2.public_tags.set([self.tag1, self.tag2])  # satisfies rule 1, rule 2
        self.e3.public_tags.set(
            [self.tag7, self.tag4, self.tag5, self.tag6]
        )  # satisfies rule 3
        self.e4.public_tags.set(
            [self.tag7, self.tag4, self.tag5, self.tag8]  # satisfies rule 3
        )
        self.e5.public_tags.set(
            [
                self.tag7,
                self.tag4,
                self.tag6,
                self.tag1,
            ]  # satisfies rule 2 and rule 3
        )
        self.e6.public_tags.set([self.tag9, self.tag8])  # satisfies rule 4

    def rec_validate_sub_slots(self, parent, assessment_slot, submission_slot):
        for sub_slot in parent.sub_slots.all():
            sub_assessment_slot = assessment_slot.sub_slots.get(
                slot_number=sub_slot.slot_number
            )
            self.assertEqual(
                sub_slot.exercise,
                sub_assessment_slot.exercise,
            )
            self.assertEqual(
                sub_slot.get_assessment(
                    assessment_slot.assessment.participation
                ).exercise.pk,
                sub_slot.exercise.pk,
            )

            sub_submission_slot = submission_slot.sub_slots.get(
                slot_number=sub_slot.slot_number
            )
            self.assertEqual(
                sub_slot.exercise,
                sub_submission_slot.exercise,
            )
            self.assertEqual(
                sub_slot.get_submission(
                    submission_slot.submission.participation
                ).exercise.pk,
                sub_slot.exercise.pk,
            )

            self.rec_validate_sub_slots(
                sub_slot, sub_assessment_slot, sub_submission_slot
            )

    def test_creation(self):
        for i in range(0, 10):
            user = User.objects.create(email=str(i) + "@aaa.com", username=str(i))
            participation = EventParticipation.objects.create(
                event_id=self.event.pk, user=user
            )

            slot_0 = participation.slots.base_slots().get(slot_number=0)
            self.assertIn(slot_0.exercise.pk, [self.e1.pk, self.e2.pk])

            # show that assigning an exercise from another course isn't allowed
            with self.assertRaises(ValidationError):
                slot_0.exercise = self.e1_other_course
                slot_0.save()

            # show that assigning a populating rule from another course isn't allowed
            with self.assertRaises(ValidationError):
                slot_0.populating_rule = self.rule_template_other_course
                slot_0.save()

            slot_1 = participation.slots.base_slots().get(slot_number=1)
            self.assertIn(slot_1.exercise.pk, [self.e1.pk, self.e2.pk, self.e5.pk])

            slot_2 = participation.slots.get(slot_number=2)
            self.assertIn(slot_2.exercise.pk, [self.e3.pk, self.e4.pk, self.e5.pk])

            if slot_2.exercise.pk == self.e4.pk:
                self.assertEqual(slot_2.sub_slots.count(), 2)
                # show that a sub-slot cannot be assigned a parent with an exercise that doesn't have
                # a parent exercise assigned to it
                with self.assertRaises(ValidationError):
                    sub_slot = slot_2.sub_slots.first()
                    sub_slot.parent = slot_1
                    sub_slot.save()

            slot_3 = participation.slots.get(slot_number=3)
            self.assertIn(slot_3.exercise.pk, [self.e6.pk])

            self.assertNotEqual(slot_0.exercise.pk, slot_1.exercise.pk)
            self.assertNotEqual(slot_1.exercise.pk, slot_2.exercise.pk)
