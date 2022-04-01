from django.urls import re_path

from . import consumers

websocket_patterns = [
    re_path(
        r"ws/events/$",  # (?P<event_id>\w+)/
        consumers.EventConsumer.as_asgi(),
        name="event_consumer",
    ),
    #     re_path(
    #         r"ws/exam_list/$",
    #         consumers.ExamListConsumer.as_asgi(),
    #         name="exam_list",
    #     ),
]
