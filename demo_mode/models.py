from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from users.managers import UserManager
import json
from django.utils import timezone

from datetime import timedelta


def validate_list_of_emails(value):
    if not isinstance(value, list):
        raise ValidationError("not a list: " + str(value))

    for entry in value:
        if not isinstance(entry, str):
            raise ValidationError("not a str: " + str(entry))
        EmailValidator()(entry)


class DemoUserManager(UserManager):
    @transaction.atomic()
    def create_user(self, username, email=None, password=None, **extra_fields):
        from demo_mode.logic import (
            get_invitation_for_new_user_or_raise,
            normalize_email_address,
        )
        from demo_mode.demo_management import create_demo_courses_for

        email = email or ""

        invitation: DemoInvitation = get_invitation_for_new_user_or_raise(email)
        create_courses = False

        if invitation.main_invitee_email == normalize_email_address(email):
            extra_fields.setdefault("is_teacher", True)
            create_courses = True

        user = super().create_user(username, email, password, **extra_fields)
        if create_courses:
            create_demo_courses_for(user)

        return user


class DemoInvitationManager(models.Manager):
    def get_queryset(self):
        from demo_mode.querysets import DemoInvitationQuerySet

        return DemoInvitationQuerySet(self.model, using=self._db)


class DemoInvitation(models.Model):
    """ """

    DEMO_DURATION_HOURS = 24 * 7

    (ACTIVE, EXPIRED, PENDING, REVOKED) = range(0, 4)
    STATES = (
        (ACTIVE, "Active"),
        (EXPIRED, "Expired"),
        (PENDING, "Pending"),
        (REVOKED, "Revoked"),
    )

    main_invitee_email = models.CharField(
        max_length=250,
        validators=[EmailValidator()],
        unique=True,
    )
    other_invitees_emails = models.JSONField(
        default=list,
        validators=[validate_list_of_emails],
        blank=True,
    )
    state = models.PositiveSmallIntegerField(choices=STATES, default=PENDING)
    # duration_hours = models.PositiveIntegerField(default=24 * 7)
    created = models.DateTimeField(auto_now_add=True)

    objects = DemoInvitationManager()

    def __str__(self) -> str:
        return self.main_invitee_email + " - " + json.dumps(self.other_invitees_emails)

    def save(self, *args, **kwargs) -> None:
        from demo_mode.logic import normalize_email_address

        self.main_invitee_email = normalize_email_address(self.main_invitee_email)
        self.other_invitees_emails = [
            normalize_email_address(e) for e in self.other_invitees_emails
        ]
        return super().save(*args, **kwargs)

    @property
    def expired(self):
        return self.created < timezone.now() - timedelta(
            hours=DemoInvitation.DEMO_DURATION_HOURS
        )
