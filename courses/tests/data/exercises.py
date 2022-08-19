from courses.models import Exercise


msc_priv_1 = {
    "text": "multiple choice single selection private 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
    "state": Exercise.PRIVATE,
    "solution": "solution of multiple choice single selection private 1",
    "choices": [
        {
            "text": "correct",
            "correctness": "1",
        },
        {
            "text": "partially correct",
            "correctness": "0.5",
        },
        {
            "text": "incorrect",
            "correctness": "0",
        },
    ],
}


msc_pub_1 = {
    "text": "multiple choice single selection public 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
    "state": Exercise.PUBLIC,
    "solution": "solution of multiple choice single selection public 1",
    "choices": [
        {
            "text": "correct",
            "correctness": "1",
        },
        {
            "text": "partially correct",
            "correctness": "0.5",
        },
        {
            "text": "incorrect",
            "correctness": 0,
        },
    ],
}

mmc_priv_1 = {
    "text": "multiple choice multiple selection private 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
    "state": Exercise.PRIVATE,
    "solution": "solution of multiple choice multiple selection private 1",
    "choices": [
        {
            "text": "correct 1",
            "correctness": "1",
        },
        {
            "text": "correct 2",
            "correctness": "1",
        },
        {
            "text": "partially correct",
            "correctness": "0.5",
        },
        {
            "text": "incorrect",
            "correctness": -1,
        },
    ],
}

mmc_pub_1 = {
    "text": "multiple choice multiple selection public 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
    "state": Exercise.PUBLIC,
    "solution": "solution of multiple choice multiple selection public 1",
    "choices": [
        {
            "text": "correct",
            "correctness": "1",
        },
        {
            "text": "partially correct",
            "correctness": "0.5",
        },
        {
            "text": "incorrect",
            "correctness": 0,
        },
    ],
}

mmc_draft_1 = {
    "text": "multiple choice multiple selection draft 1",
    "exercise_type": Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
    "state": Exercise.DRAFT,
    "solution": "solution of multiple choice multiple selection public 1",
    "choices": [
        {
            "text": "correct",
            "correctness": "1",
        },
        {
            "text": "partially correct",
            "correctness": "0.5",
        },
        {
            "text": "incorrect",
            "correctness": 0,
        },
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

cloze_prv_1 = {
    "text": "Text of [[?]] the cloze [[?]] question, [[?]].",
    "exercise_type": Exercise.COMPLETION,
    "state": Exercise.PRIVATE,
    "sub_exercises": [
        {
            "text": "",
            "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            "child_weight": 2,
            "choices": [
                {"text": "correct", "correctness": 1},
                {"text": "partially_correct", "correctness": 0.5},
                {"text": "incorrect", "correctness": 0},
            ],
        },
        {
            "text": "",
            "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            "child_weight": 1,
            "choices": [
                {"text": "correct", "correctness": 1},
                {"text": "partially_correct", "correctness": 0.5},
                {"text": "incorrect", "correctness": -0.1},
            ],
        },
        {
            "text": "",
            "exercise_type": Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            "child_weight": 1,
            "choices": [
                {"text": "correct", "correctness": 1},
                {"text": "partially_correct", "correctness": 0.5},
                {"text": "incorrect", "correctness": 0},
            ],
        },
    ],
}


js_prv_1 = {
    "text": "js private 1",
    "exercise_type": Exercise.JS,
    "state": Exercise.PRIVATE,
    "testcases": [
        {
            "code": "123",
        },
        {
            "code": "456",
        },
        {
            "code": "789",
        },
        {
            "code": "012",
        },
    ],
}
