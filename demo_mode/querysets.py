from locale import normalize
from django.db import models
from demo_mode.models import DemoInvitation
from users.models import User
from .logic import is_demo_mode, normalize_email_address
from django.db.models import Exists, OuterRef
from django.db.models import Q


class DemoInvitationQuerySet(models.QuerySet):
    def valid(self):
        return self.exclude(state__in=[DemoInvitation.REVOKED, DemoInvitation.EXPIRED])

    def valid_for(self, user: User):
        normalized_email = normalize_email_address(user.email)
        return self.valid().filter(
            main_invitee_email=normalized_email,
            other_invitees_emails__contains=normalized_email,
        )


class DemoCoursesQuerySet(models.QuerySet):
    def visible_in_demo_mode_to(self, user: User):
        valid_invitations = DemoInvitation.objects.all().valid()
        # TODO optimize
        pks = []
        for course in self:
            if course.creator == user or normalize_email_address(user.email) in [
                email
                for sublist in [d.other_invitees_emails for d in valid_invitations]
                for email in sublist
            ]:
                pks.append(course.pk)

        return self.filter(pk__in=pks)
