from abc import ABC, abstractmethod
from decimal import Decimal
from django.utils.module_loading import import_string
from typing import Optional
from courses.logic.registries import get_exercise_logic_registry

from courses.logic.submission import ExerciseSubmission
from ..models import Exercise, ExerciseChoice
from django.db.models import F, Max, Q


class ExerciseLogic(ABC):
    exercise: Exercise

    def __init__(self, exercise: Exercise) -> None:
        self.exercise = exercise

    @staticmethod
    def get_exercise_logic_class(exercise_type):
        cls_name = get_exercise_logic_registry()[exercise_type]
        return import_string(cls_name)

    @staticmethod
    def from_exercise_instance(exercise: Exercise) -> "ExerciseLogic":
        cls = ExerciseLogic.get_exercise_logic_class(exercise.exercise_type)
        return cls(exercise=exercise)

    @abstractmethod
    def get_max_score(self) -> Decimal:
        ...

    @abstractmethod
    def get_grade(self, submission: ExerciseSubmission) -> Optional[Decimal]:
        ...

    @abstractmethod
    def has_answer(self, submission: ExerciseSubmission) -> bool:
        ...


class ManuallyGradedExerciseLogic(ExerciseLogic):
    def get_grade(self, submission: ExerciseSubmission) -> Optional[Decimal]:
        return None if self.has_answer(submission) else Decimal(0)


class MultipleChoiceExerciseLogic(ExerciseLogic):
    def has_answer(self, submission: ExerciseSubmission) -> bool:
        return submission.has_execution_results

    def get_grade(self, submission: ExerciseSubmission) -> Optional[Decimal]:
        selected_choices = submission.selected_choices.all()
        return Decimal(sum([c.correctness for c in selected_choices]))

    def get_max_score(self):
        correct_choices = self.exercise.choices.filter(correctness__gt=0)
        return Decimal(sum([c.correctness for c in correct_choices]))


class MultipleChoiceSingleSelectionExerciseLogic(MultipleChoiceExerciseLogic):
    def get_max_score(self):
        if hasattr(self.exercise, "prefetched_max_choice_correctness"):
            max_score = self.exercise.prefetched_max_choice_correctness
        else:
            max_score = (self.exercise.choices.all().aggregate(Max("correctness")))[
                "correctness__max"
            ]  # TODO `or 0`?
        return Decimal(max_score)


class ProgrammingExerciseLogic(ExerciseLogic):
    def has_answer(self, submission: ExerciseSubmission) -> bool:
        return submission.has_answer_text

    # def get_grade(self, submission: ExerciseSubmission) -> Optional[Decimal]:
    #     return super().get_grade(submission)

    # def get_max_score(self):
    #     return super().get_max_score()


class OpenAnswerExerciseLogic(ManuallyGradedExerciseLogic):
    def has_answer(self, submission: ExerciseSubmission) -> bool:
        return submission.has_answer_text


class AggregatedExerciseLogic(ExerciseLogic):
    pass


class CompletionExerciseLogic(ExerciseLogic):
    pass


class AttachmentExerciseLogic(ManuallyGradedExerciseLogic):
    def has_answer(self, submission: ExerciseSubmission) -> bool:
        return submission.has_attachment
