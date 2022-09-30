from demo_mode.models import DemoInvitation
from django.conf import settings
from django.core.exceptions import ValidationError


# def is_course_accessible_in_demo_mode(course: Course, user: User) -> bool:
#     return True


def is_demo_mode() -> bool:
    return settings.DEMO_MODE


def normalize_email_address(value: str) -> str:
    # TODO implement
    return value


def get_invitation_for_new_user_or_raise(user_email: str):
    valid_invitations = DemoInvitation.objects.all().valid_for(user_email)
    if not valid_invitations.exists():
        raise ValidationError(
            "User " + user_email + " doesn't have a valid invitation."
        )

    return valid_invitations.order_by("-created").first()
