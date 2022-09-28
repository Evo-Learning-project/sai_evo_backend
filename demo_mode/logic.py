from courses.models import Course
from users.models import User
from django.conf import settings


def is_course_accessible_in_demo_mode(course: Course, user: User) -> bool:
    return True


def is_demo_mode() -> bool:
    return settings.DEMO_MODE
