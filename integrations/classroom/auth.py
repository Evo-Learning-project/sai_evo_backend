from typing import Literal, Optional, Union
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow

from integrations.classroom.integration import GoogleClassroomIntegration

from django.conf import settings

from users.models import User


def get_flow(scope_role: Optional[Union[Literal["teacher"], Literal["student"]]]):
    from integrations.classroom.views import GoogleClassroomViewSet

    """
    If `no_scopes` is True, the value `None` will be passed to `Flow` instead of the list of scopes.
    See https://stackoverflow.com/a/52085446/12424975
    """
    scopes = (
        GoogleClassroomIntegration.TEACHER_SCOPES
        if scope_role == "teacher"
        else GoogleClassroomIntegration.STUDENT_SCOPES
        if scope_role == "student"
        else None
    )

    flow = Flow.from_client_config(
        GoogleClassroomIntegration().get_client_config(),
        scopes=scopes,
    )
    # TODO get url from router
    flow.redirect_uri = (
        settings.BASE_BACKEND_URL + "/integrations/classroom/oauth2_callback"
    )
    return flow


def get_auth_request_url(
    user: Union[User, None], scope_role: Union[Literal["teacher"], Literal["student"]]
):
    flow = get_flow(scope_role=scope_role)

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    # flow.redirect_uri = settings.BASE_BACKEND_URL + "/integrations/classroom/callback"

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type="offline",
        prompt="consent",
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
        login_hint=user.email if user is not None else None,
    )

    # TODO `state` should also be used for better security
    return authorization_url
