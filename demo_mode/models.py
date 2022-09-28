from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from demo_mode.logic import normalize_email_address


def validate_list_of_emails(value):
    if not isinstance(value, list):
        raise ValidationError("not a list: " + str(value))

    for entry in value:
        if not isinstance(entry, str):
            raise ValidationError("not a str: " + str(entry))
        EmailValidator()(entry)


class DemoInvitationManager(models.Manager):
    def get_queryset(self):
        from demo_mode.querysets import DemoInvitationQuerySet

        return DemoInvitationQuerySet(self.model, using=self._db)


class DemoInvitation(models.Model):
    """ """

    (ACTIVE, EXPIRED, PENDING, REVOKED) = range(0, 4)
    STATES = (
        (ACTIVE, "Active"),
        (EXPIRED, "Expired"),
        (PENDING, "Pending"),
        (REVOKED, "Revoked"),
    )

    main_invitee_email = models.CharField(max_length=250, validators=[EmailValidator()])
    other_invitees_emails = models.JSONField(
        default=list, validators=[validate_list_of_emails]
    )
    state = models.PositiveSmallIntegerField(choices=STATES, default=PENDING)
    duration_hours = models.PositiveIntegerField(default=24 * 7)
    created = models.DateTimeField(auto_now_add=True)

    objects = DemoInvitationManager()

    def save(self, *args, **kwargs) -> None:
        self.main_invitee_email = normalize_email_address(self.main_invitee_email)
        self.other_invitees_emails = [
            normalize_email_address(e) for e in self.other_invitees_emails
        ]
        return super().save(*args, **kwargs)
