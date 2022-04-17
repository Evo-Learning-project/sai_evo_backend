from django.db import models
from django.db.models import Count, Q
from django.db.models.aggregates import Max, Min
from django.db.models import Count, Case, When, IntegerField


class UserQuerySet(models.QuerySet):
    def active_in_course(self, course_id):
        """
        Returns the users that have participated in at least one event
        in the given course
        """
        # return self.annotate(
        #     exists_participation_in_course=Count(
        #         Case(
        #             When(
        #                 participations__event_instance__event__course_id=course_id,
        #                 then=1,
        #             ),
        #             output_field=IntegerField(),
        #         )
        #     )
        # ).filter(exists_participation_in_course__gt=0)
        return self.annotate(
            participation_count=Count(
                "participations",
                filter=Q(participations__event__course_id=course_id),
            )
        ).filter(participation_count__gt=0)
