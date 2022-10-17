from abc import ABC, abstractmethod
from decimal import Decimal
from ..models import Exercise


class ExerciseLogic(ABC):
    @staticmethod
    def from_exercise_instance(exercise: Exercise) -> "ExerciseLogic":
        ...

    @abstractmethod
    def get_max_score(self):
        ...

    @abstractmethod
    def get_grade(self, submission) -> Decimal:
        ...

    @abstractmethod
    def has_answer(self, submission) -> bool:
        ...


class MultipleChoiceExerciseLogic(ExerciseLogic):
    pass


class MultipleChoiceSingleSelectionExerciseLogic(MultipleChoiceExerciseLogic):
    # overrides get_max_score
    pass


class ProgrammingExerciseLogic(ExerciseLogic):
    pass


class OpenAnswerExerciseLogic(ExerciseLogic):
    pass


class AggregatedExerciseLogic(ExerciseLogic):
    pass


class ClozeExerciseLogic(ExerciseLogic):
    pass


class AttachmentExerciseLogic(ExerciseLogic):
    pass
