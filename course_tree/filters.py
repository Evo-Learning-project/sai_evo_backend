import django_filters
from django_filters.rest_framework import FilterSet

from course_tree.models import BaseCourseTreeNode


class CourseTreeNodeFilter(FilterSet):
    resourcetype = django_filters.CharFilter(method="resourcetype_filter")

    class Meta:
        model = BaseCourseTreeNode
        fields = []
        # fields = ["resource_type"]

    def resourcetype_filter(self, queryset, name, value):
        if value:
            if value.lower() not in [
                "topicnode",
                "lessonnode",
                "filenode",
                "announcementnode",
            ]:
                return queryset.none()
            filter_cond = {value.lower() + "__isnull": False}
            queryset = queryset.filter(**filter_cond)
        return queryset
