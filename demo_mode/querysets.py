from locale import normalize
from django.db import models
from demo_mode.models import DemoInvitation
from users.models import User
from .logic import is_demo_mode, normalize_email_address
from django.db.models import Exists, OuterRef
from django.db.models import Q, F
from django.utils import timezone

from datetime import timedelta


class DemoInvitationQuerySet(models.QuerySet):
    def valid(self):
        return self.filter(
            created__gte=timezone.now()
            - timedelta(hours=DemoInvitation.DEMO_DURATION_HOURS)
        ).exclude(state__in=[DemoInvitation.REVOKED, DemoInvitation.EXPIRED])

    def valid_for(self, user_email: str):
        from django.conf import settings

        normalized_email = normalize_email_address(user_email)
        if not settings.DEBUG:
            return self.valid().filter(
                Q(main_invitee_email=normalized_email)
                | (
                    # `contains` lookup not supported by sqlite
                    Q(other_invitees_emails__contains=[normalized_email])
                )
            )
        # workaround to test with sqlite
        pks = []
        for invitation in self.valid():
            if (
                invitation.main_invitee_email == normalized_email
                or normalized_email in invitation.other_invitees_emails
            ):
                pks.append(invitation.pk)
        return self.filter(pk__in=pks)


class DemoCoursesQuerySet(models.QuerySet):
    def visible_in_demo_mode_to(self, user: User):
        valid_invitations = DemoInvitation.objects.all().valid()
        pks = []
        for course in self:
            if course.creator == user or normalize_email_address(user.email) in [
                email
                for sublist in [
                    d.other_invitees_emails
                    for d in valid_invitations.filter(
                        main_invitee_email=normalize_email_address(course.creator.email)
                    )
                ]
                for email in sublist
            ]:
                pks.append(course.pk)

        return self.filter(pk__in=pks)
