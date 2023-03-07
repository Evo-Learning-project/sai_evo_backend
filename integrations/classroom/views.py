from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from integrations.classroom import auth
from django.conf import settings

from social_core.backends.google import GoogleOAuth2

from rest_access_policy import AccessPolicy

import logging
from integrations.classroom.exceptions import (
    InvalidGoogleOAuth2Credentials,
    MissingGoogleOAuth2Credentials,
)
from integrations.classroom.integration import GoogleClassroomIntegration

from integrations.models import GoogleOAuth2Credentials
from users.models import User

from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer


logger = logging.getLogger(__name__)


class GoogleClassroomAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["oauth2_callback"],
            "principal": ["*"],
            "effect": "allow",
        },
        {
            "action": ["authorized_scopes", "auth_url"],
            "principal": ["authenticated"],
            "effect": "allow",
        },
    ]


class GoogleClassroomViewSet(viewsets.ViewSet):
    permission_classes = [GoogleClassroomAccessPolicy]

    def get_renderers(self):
        if self.action == "oauth2_callback":
            return [StaticHTMLRenderer()]
        return super().get_renderers()

    # TODO verify if only "get" is sufficient
    @action(methods=["get", "post", "put"], detail=False)
    def oauth2_callback(self, request, *args, **kwargs):
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
            # use returned token to fetch user profile and determine whom
            # to associate the credentials to
            user_profile = GoogleOAuth2().user_data(
                access_token=response["access_token"]
            )
        except Exception as e:
            logger.exception("Google OAuth callback failed to fetch token")
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            email = user_profile.get("email", "")
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.critical(
                "Google OAuth callback failed to find user with email " + str(email)
            )
            return Response(status=status.HTTP_404_NOT_FOUND)

        # keep data we're interested in
        keys = ["access_token", "refresh_token", "scope", "id_token"]
        data = {key: response[key] for key in keys}
        # create credentials object and associate it to user
        GoogleOAuth2Credentials.objects.update_or_create(user=user, defaults=data)

        # this view will be reached directly by the user's browser since
        # it'll be accessed through the redirect_uri param of google oauth.
        # return a response with a script that closes the page
        return Response(
            """
                        <html>
                            <body>Success!</body>
                            <script type="text/javascript">
                                window.close()
                            </script>
                        </html>
            """
        )

    @action(methods=["get"], detail=False)
    def authorized_scopes(self, request, *args, **kwargs):
        try:
            creds = GoogleClassroomIntegration().get_credentials(user=request.user)
            scopes = creds.scopes
        except MissingGoogleOAuth2Credentials:
            scopes = []
        except InvalidGoogleOAuth2Credentials:
            logger.critical("Invalid credentials for user " + str(request.user.pk))
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(data=scopes, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def auth_url(self, request, *args, **kwargs):
        url = auth.get_auth_request_url(user=request.user)
        return Response(data=url, status=status.HTTP_200_OK)
