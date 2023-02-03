from django.db import models
from django.db.models import Count, Q, Exists
from django.db.models.aggregates import Max, Min
from django.db.models import Count, Case, When, IntegerField


class UserQuerySet(models.QuerySet):
    def active_in_course(self, course_id):
        """
        Returns the users that have participated in at least one event
        in the given course
        """
        return self.annotate(
            participation_count=Count(
                "participations",
                filter=Q(participations__event__course_id=course_id),
            )
        ).filter(participation_count__gt=0)

    def with_privileges_in_course(self, course_id):
        """
        Returns the users which have a UserCoursePrivilege object associated to them
        and the given course, and which has at least one allowed privilege
        """
        # TODO this will change if Roles are ever officially added

        return self.annotate(
            privileges_count=Count(
                "privileged_courses",
                filter=Q(privileged_courses__course_id=course_id)
                & ~Q(privileged_courses__allow_privileges=[]),
            )
        ).filter(privileges_count__gt=0)
