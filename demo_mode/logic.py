from users.models import User
from django.conf import settings


# def is_course_accessible_in_demo_mode(course: Course, user: User) -> bool:
#     return True


def is_demo_mode() -> bool:
    print("DEMO", settings.DEMO_MODE)
    return settings.DEMO_MODE


def normalize_email_address(value: str) -> str:
    return value
