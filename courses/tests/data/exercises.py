from courses.models import Exercise


msc_priv_1 = {
    "text": "multiple choice single selection private 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
    "state": Exercise.PRIVATE,
    "solution": "solution of multiple choice single selection private 1",
    "choices": [
        {"text": "correct", "score_selected": "1.00", "score_unselected": "0.00"},
        {
            "text": "partially correct",
            "score_selected": "0.50",
            "score_unselected": "0.00",
        },
        {"text": "incorrect", "score_selected": "0.00", "score_unselected": "-0.50"},
    ],
}


msc_pub_1 = {
    "text": "multiple choice single selection public 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
    "state": Exercise.PUBLIC,
    "solution": "solution of multiple choice single selection public 1",
    "choices": [
        {"text": "correct", "score_selected": "1.00", "score_unselected": "0.00"},
        {
            "text": "partially correct",
            "score_selected": "0.50",
            "score_unselected": "0.00",
        },
        {"text": "incorrect", "score_selected": "0.00", "score_unselected": "-0.50"},
    ],
}

mmc_priv_1 = {
    "text": "multiple choice multiple selection private 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
    "state": Exercise.PRIVATE,
    "solution": "solution of multiple choice multiple selection private 1",
    "choices": [
        {"text": "correct", "score_selected": "1.00", "score_unselected": "0.00"},
        {
            "text": "partially correct",
            "score_selected": "0.50",
            "score_unselected": "0.00",
        },
        {"text": "incorrect", "score_selected": "0.00", "score_unselected": "-0.50"},
    ],
}

mmc_pub_1 = {
    "text": "multiple choice multiple selection private 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
    "state": Exercise.PUBLIC,
    "solution": "solution of multiple choice multiple selection public 1",
    "choices": [
        {"text": "correct", "score_selected": "1.00", "score_unselected": "0.00"},
        {
            "text": "partially correct",
            "score_selected": "0.50",
            "score_unselected": "0.00",
        },
        {"text": "incorrect", "score_selected": "0.00", "score_unselected": "-0.50"},
    ],
}


open_priv_1 = {
    "text": "open private 1",
    "exercise_type": Exercise.OPEN_ANSWER,
    "state": Exercise.PRIVATE,
    "solution": "solution of open private 1",
}

open_pub_1 = {
    "text": "open public 1",
    "exercise_type": Exercise.OPEN_ANSWER,
    "state": Exercise.PUBLIC,
    "solution": "solution of open public 1",
}
