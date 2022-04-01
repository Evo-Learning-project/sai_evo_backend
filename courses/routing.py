from django.urls import re_path

from . import consumers

websocket_patterns = [
    #     re_path(
    #         r"ws/exam_lock/(?P<exam_id>\w+)/$",
    #         consumers.ExamLockConsumer.as_asgi(),
    #         name="exam_lock",
    #     ),
    #     re_path(
    #         r"ws/exam_list/$",
    #         consumers.ExamListConsumer.as_asgi(),
    #         name="exam_list",
    #     ),
]
