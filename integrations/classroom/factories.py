from typing import Union
from django.utils.html import strip_tags


def get_material_payload(title, description, material_url):
    # TODO handle empty title
    return {
        "title": title,
        "description": description,
        "state": "PUBLISHED",
        "materials": [
            {"link": {"url": material_url}},
        ],
        # "topicId": topicId
    }


def get_announcement_payload(text, announcement_url):
    return {
        "text": strip_tags(text),
        "state": "PUBLISHED",
        "assigneeMode": "ALL_STUDENTS",
        "materials": [
            {"link": {"url": announcement_url}},
        ],
    }


def get_assignment_payload(
    title: str, description: str, exam_url: str, scheduled_timestamp: Union[str, None]
):
    return {
        "title": strip_tags(title),
        "description": strip_tags(description),
        "materials": [
            {"link": {"url": exam_url}},
        ],
        "workType": "ASSIGNMENT",
        "state": "DRAFT" if scheduled_timestamp else "PUBLISHED",
        "scheduledTime": scheduled_timestamp,
    }
