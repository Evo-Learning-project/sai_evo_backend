from collections import OrderedDict

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class LeaderboardPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "size"

    def paginate_queryset(self, queryset, request, view=None):
        """
        Taken from https://stackoverflow.com/a/31695256/12424975
        """
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except NotFound:  # intercept NotFound exception and return empty list instead of 404
            return list()

    def get_paginated_response(self, data):
        """Avoid case when self does not have page properties for empty list"""
        if hasattr(self, "page") and self.page is not None:
            return super().get_paginated_response(data)
        else:
            return Response(
                OrderedDict(
                    [
                        ("count", None),
                        ("next", None),
                        ("previous", None),
                        ("results", data),
                    ]
                )
            )
