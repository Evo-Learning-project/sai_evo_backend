from courses.models import Event

exam_1_all_at_once = {
    "name": "exam_1",
    "event_type": Event.EXAM,
    "exercises_shown_at_a_time": None,
    "state": Event.DRAFT,
}

exam_1_one_at_a_time = {
    "name": "exam_1",
    "event_type": Event.EXAM,
    "exercises_shown_at_a_time": 1,
    "state": Event.DRAFT,
}
