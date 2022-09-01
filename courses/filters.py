import django_filters
from django_filters.rest_framework import FilterSet

from courses.models import EventParticipation, Exercise, ExerciseSolution, Tag, Event
from django.db.models import Q


class ExerciseFilter(FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(), method="tags_filter"
    )
    with_submitted_solutions = django_filters.BooleanFilter(
        method="with_submitted_solutions_filter"
    )
    with_bookmarked_solutions = django_filters.BooleanFilter(
        method="with_bookmarked_solutions_filter"
    )
    by_popularity = django_filters.BooleanFilter(method="order_by_popularity")

    class Meta:
        model = Exercise
        fields = ["tags", "exercise_type", "state"]

    def tags_filter(self, queryset, name, value):
        for tag in value:
            filter_cond = Q(public_tags__in=[tag]) | Q(private_tags__in=[tag])
            queryset = queryset.filter(filter_cond).distinct()
        return queryset

    def with_submitted_solutions_filter(self, queryset, name, value):
        if value:
            queryset = queryset.with_submitted_solutions()
        return queryset

    def with_bookmarked_solutions_filter(self, queryset, name, value):
        if value:
            queryset = queryset.with_solutions_bookmarked_by(self.request.user)
        return queryset

    def order_by_popularity(self, queryset, name, value):
        if value:
            queryset = queryset.order_by_popularity()
        return queryset


class ExerciseSolutionFilter(FilterSet):
    bookmarked = django_filters.BooleanFilter(method="bookmarked_filter")

    class Meta:
        model = ExerciseSolution
        fields = ["state"]

    def bookmarked_filter(self, queryset, name, value):
        if value:
            queryset = queryset.bookmarked_by(self.request.user)
        return queryset


class EventFilter(FilterSet):
    class Meta:
        model = Event
        fields = ["event_type"]


class EventParticipationFilter(FilterSet):
    bookmarked = django_filters.BooleanFilter(method="bookmarked_filter")
    event_type = django_filters.NumberFilter(method="event_type_filter")

    class Meta:
        model = EventParticipation
        fields = ["bookmarked"]

    def bookmarked_filter(self, queryset, name, value):
        if value:
            queryset = queryset.filter(bookmarked=True)
        return queryset

    def event_type_filter(self, queryset, name, value):
        if value:
            queryset = queryset.filter(event__event_type=value)
        return queryset
