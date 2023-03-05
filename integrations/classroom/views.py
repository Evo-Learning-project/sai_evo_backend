from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from integrations.classroom import auth
from django.conf import settings


import logging

logger = logging.getLogger(__name__)


class GoogleClassroomViewSet(viewsets.ViewSet):
    # TODO verify if only "get" is sufficient
    @action(methods=["get", "post", "put"], detail=False)
    def callback(self, request, *args, **kwargs):
        """
        Callback view that gets called by Google upon the user completing the
        authentication flow. This view is specifically used for incremental auth
        and will be called when the user grants additional permissions in order
        to allow Evo access to Google Classroom resources owned by the user
        """
        request_url = settings.BASE_BACKEND_URL + request.get_full_path()

        # see comment on `get_flow` about the `no_scopes` arg
        flow = auth.get_flow(no_scopes=True)

        try:
            response = flow.fetch_token(authorization_response=request_url)
            token, refresh_token = response["token"], response["refresh_token"]
        except Exception as e:
            logger.critical("Google OAuth callback failed to fetch token: " + str(e))
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # TODO use token and refresh token to create token model instance

        return Response(status=status.HTTP_200_OK)
