from courses.models import Course, Exercise
from django.core.exceptions import ValidationError
from django.test import TestCase


class ExerciseManagerTestCase(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="test_course")
        self.e1_text = "aaa"

    def test_multiple_choice_single_possible_exercise_creation(self):
        # supplying choices together with the exercise data creates the choices
        # related to that exercise
        choices = [
            {"text": "c1", "correct": True},
            {"text": "c2", "correct": False},
            {"text": "c3", "correct": False},
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
            [{"text": c.text, "correct": c.correct} for c in e1.choices.all()],
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
            {"text": "c1", "correct": True},
            {"text": "c2", "correct": False},
            {"text": "c3", "correct": False},
        ]

        e1 = Exercise.objects.create(
            text=self.e1_text,
            choices=choices,
            exercise_type=Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            course=self.course,
        )

        self.assertEqual(e1.text, self.e1_text)
        self.assertEqual(e1.exercise_type, Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE)
        self.assertEqual(  # one sub-exercise is created for each choice
            e1.sub_exercises.count(),
            len(choices),
        )
        self.assertEqual(  # no choices are directly related to the parent exercise
            e1.choices.count(), 0
        )

        i = 0
        for sub_exercise in e1.sub_exercises.all():
            # the automatically created sub-exercises have empty text
            self.assertEqual(sub_exercise.text, "")

            # the automatically created sub-exercises have a single choice
            self.assertEqual(sub_exercise.choices.count(), 1)

            choice = sub_exercise.choices.first()
            # the created choices are the same ones supplied for the parent exercise
            self.assertEqual(
                {"text": choice.text, "correct": choice.correct}, choices[i]
            )
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
                choices=[{"text": "c1", "correct": True}],
                exercise_type=Exercise.OPEN_ANSWER,
                course=self.course,
            )

    def test_completion_exercise_creation(self):
        choices = [  # choices are supplied as a list of lists
            [
                {"text": "1c1", "correct": True},
                {"text": "1c2", "correct": False},
            ],
            [
                {"text": "2c1", "correct": False},
                {"text": "2c2", "correct": True},
            ],
            [
                {"text": "3c1", "correct": False},
                {"text": "3c2", "correct": True},
                {"text": "3c3", "correct": False},
            ],
        ]

        e1 = Exercise.objects.create(
            text=self.e1_text,
            choices=choices,
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
                        "correct": c.correct,
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
                {"text": "1c1", "correct": True},
                {"text": "1c2", "correct": False},
            ],
        }
        sub_e2 = {
            "text": "sub2",
            "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
            "choices": [
                {"text": "2c1", "correct": True},
                {"text": "2c2", "correct": False},
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
                    {"text": "aaa", "correct": True},
                    {"text": "ccc", "correct": False},
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
                choices=[{"text": "c1", "correct": True}],
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
