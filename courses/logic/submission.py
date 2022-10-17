from dataclasses import dataclass
from typing import Any, Optional
from ..models import EventParticipationSlot, ExerciseChoice
from django.db.models.fields.files import FieldFile
from django.db.models import QuerySet


@dataclass
class ExerciseSubmission:
    answer_text: str
    selected_choices: QuerySet[ExerciseChoice]  # TODO use iterable
    execution_results: Any  # TODO make interface
    attachment: Optional[FieldFile]

    @classmethod
    def from_event_participation_slot(cls, slot: EventParticipationSlot):
        return cls(
            answer_text=slot.answer_text,
            selected_choices=slot.selected_choices,
            execution_results=slot.execution_results,
            attachment=slot.attachment,
        )

    @property
    def has_answer_text(self):
        return bool(self.has_answer_text)

    @property
    def has_selected_choices(self):
        return self.selected_choices.exists()

    @property
    def has_attachment(self):
        return bool(self.attachment)

    @property
    def has_execution_results(self):
        return self.execution_results is not None
