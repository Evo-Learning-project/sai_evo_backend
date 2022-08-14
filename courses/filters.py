import django_filters
from django_filters.rest_framework import FilterSet

from courses.models import (
    Exercise,
    ExerciseSolution,
    Tag,
)
from django.db.models import Q


class ExerciseFilter(FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(), method="tags_filter"
    )
    with_submitted_solutions = django_filters.BooleanFilter(
        method="with_submitted_solutions_filter"
    )

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


class ExerciseSolutionFilter(FilterSet):
    class Meta:
        model = ExerciseSolution
        fields = ["state"]
