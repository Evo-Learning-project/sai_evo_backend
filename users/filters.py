import django_filters

from django_filters.rest_framework import FilterSet


class UserFilter(FilterSet):
    is_teacher = django_filters.BooleanFilter(method="is_teacher_filter")
    has_privileges = django_filters.BooleanFilter(method="has_privileges_filter")

    def is_teacher_filter(self, queryset, name, value):
        if value:
            queryset = queryset.filter(is_teacher=True)
        return queryset

    def has_privileges_filter(self, queryset, name, value):
        course_id = self.request.query_params.get("course_id", None)
        if value and course_id is not None:
            queryset = queryset.with_privileges_in_course(course_id=course_id)
        return queryset
