from dataclasses import dataclass
from typing import Any, Iterable
from ..models import ExerciseChoice


@dataclass
class ExerciseSubmission:
    answer_text: str
    selected_choices: Iterable[ExerciseChoice]
    execution_results: Any  # TODO make interface
