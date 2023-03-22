from datetime import datetime, timedelta
from decimal import Decimal
from typing import Union
from django.utils.html import strip_tags
from django.utils import timezone
from math import ceil


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
    title: str,
    description: str,
    exam_url: str,
    scheduled_timestamp: Union[datetime, None],
    max_score: Union[int, Decimal],
):
    # TODO keep an eye on timezone issues
    now = timezone.localtime(timezone.now())
    # if no `scheduled_timestamp` is provided, or if the value provided is too close
    # to the current time, we're setting the state to PUBLISHED from the start, because
    # the Classroom API will reject the request if the `scheduledTime` field ends
    # up being in the past
    publish_immediately = (
        scheduled_timestamp is None
        or (timezone.localtime(scheduled_timestamp) - (now)).total_seconds() < 60
    )

    return {
        "title": strip_tags(title),
        "description": strip_tags(description),
        "materials": [
            {"link": {"url": exam_url}},
        ],
        "workType": "ASSIGNMENT",
        "state": "PUBLISHED" if publish_immediately else "DRAFT",
        # the Classroom API only accepts integers for maxPoints:
        # see https://developers.google.com/classroom/reference/rest/v1/courses.courseWork
        # we use `ceil` to prevent edge cases where a submission would end up having a grade
        # higher than the maximum for the exam (submissions do allow decimal grades)
        "maxPoints": ceil(max_score),
        **(
            {}
            if publish_immediately
            else {"scheduledTime": scheduled_timestamp.isoformat()}
        ),
    }
