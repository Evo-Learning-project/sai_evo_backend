from rest_framework.fields import Field
from rest_framework.settings import api_settings


class PaginatedRelationField(Field):
    # taken from:
    # https://groups.google.com/g/django-rest-framework/c/QZ6-qmTMLcA/m/gg9excYdAwAJ
    # usage: fieldname = PaginatedRelationField(OtherSerializer, paginator=RelationPaginator)

    # this could also be relevant: https://stackoverflow.com/a/23541635/12424975

    def __init__(self, serializer, filters=None, paginator=None, **kwargs):

        self.serializer = serializer

        if paginator is None:
            paginator = api_settings.DEFAULT_PAGINATION_CLASS

        self.paginator = paginator()

        # Filters should be a dict, for example: {'pk': 1}
        self.filters = filters

        super(PaginatedRelationField, self).__init__(**kwargs)

    def to_representation(self, related_objects):
        if self.filters:
            related_objects = related_objects.filter(**self.filters)

        request = self.context.get("request")

        serializer = self.serializer(
            related_objects, many=True, context={"request": request}
        )

        paginated_data = self.paginator.paginate_queryset(
            queryset=serializer.data, request=request
        )

        result = self.paginator.get_paginated_response(paginated_data)

        return result
