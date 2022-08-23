import random
import string
from courses.models import Exercise
from . import js_dfl
from django.template import Context, Template


def get_random_identifier(length=20):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


class ProgrammingExerciseTemplateCompiler:
    def __init__(self, exercise: Exercise, code: str) -> None:
        self.exercise = exercise
        self.code = code

    def get_default_template_by_language(self):
        # TODO implement
        return js_dfl.DFL_ALL_TESTCASES_JS_TEMPLATE

    def get_template_context(self):
        context = {}

        context["USER_CODE"] = self.code
        context["TESTCASES"] = [t for t in self.exercise.testcases.all()]

        # generate 20 random identifiers for usage inside the template
        for i in range(0, 20):
            context["ID_" + str(i + 1)] = get_random_identifier()

        return context

    def get_template(self) -> str:
        template_str = (
            "{% autoescape off %}"
            + self.get_default_template_by_language()
            + "{% endautoescape %}"
        )
        context_dict = self.get_template_context()

        return Template(template_str).render(Context(context_dict))
