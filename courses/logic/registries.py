from ..models import Exercise


def get_exercise_logic_registry():
    std_module = "courses.logic.exercise_logic."

    return {
        Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE: std_module
        + "MultipleChoiceExerciseLogic",
        Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE: std_module
        + "MultipleChoiceSingleSelectionExerciseLogic",
        Exercise.OPEN_ANSWER: std_module + "OpenAnswerExerciseLogic",
        Exercise.JS: std_module + "ProgrammingExerciseLogic",
        Exercise.C: std_module + "ProgrammingExerciseLogic",
        Exercise.PYTHON: std_module + "ProgrammingExerciseLogic",
        Exercise.COMPLETION: std_module + "CompletionExerciseLogic",
        Exercise.AGGREGATED: std_module + "AggregatedExerciseLogic",
        Exercise.ATTACHMENT: std_module + "AttachmentExerciseLogic",
    }
