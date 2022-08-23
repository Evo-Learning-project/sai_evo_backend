from functools import cached_property
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

    @cached_property
    def context_dict(self):
        context = {}

        context["USER_CODE"] = self.code
        context["TESTCASES"] = [t for t in self.exercise.testcases.all()]

        # generate 20 random identifiers for usage inside the template
        for i in range(0, 20):
            context["ID_" + str(i + 1)] = get_random_identifier()

        # inject language-specific context
        context.update(self.language_specific_template_context)

        return context

    @cached_property
    def language_specific_template_context(self):
        """
        Dict that contains context variables that need to be passed to the sandbox
        that will run the code.

        For example, the node sandbox provides a utility function to pretty print errors.
        Templates should use the context variable PRINT_ERROR_ID to call it; the sandbox
        also needs to know about that identifier to map the actual function to the
        identifier referred inside the template.

        """
        # TODO other languages than JS
        ret = {}
        ret["ASSERTION_ERROR_CLASS_ID"] = get_random_identifier()
        ret["ASSERT_ID"] = get_random_identifier()
        ret["PRINT_ERROR_ID"] = get_random_identifier()

        return ret

    def get_default_template_by_language(self):
        # TODO implement
        return js_dfl.DFL_ALL_TESTCASES_JS_TEMPLATE

    def get_template(self) -> str:
        template_str = (
            "{% autoescape off %}"
            # TODO check if exercise has a template of its own
            + self.get_default_template_by_language()
            + "{% endautoescape %}"
        )

        return Template(template_str).render(Context(self.context_dict))
