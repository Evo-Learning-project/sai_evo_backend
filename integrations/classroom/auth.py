import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow

from integrations.classroom.integration import GoogleClassroomIntegration

from django.conf import settings


def get_flow(no_scopes=False):
    from integrations.classroom.views import GoogleClassroomViewSet

    """
    If `no_scopes` is True, the value `None` will be passed to `Flow` instead of the list of scopes.
    See https://stackoverflow.com/a/52085446/12424975
    """
    flow = Flow.from_client_config(
        GoogleClassroomIntegration().get_client_config(),
        # TODO may need to parametrize this e.g. for student flow vs teacher
        scopes=None if no_scopes else GoogleClassroomIntegration.SCOPES,
    )
    # TODO get url from router
    flow.redirect_uri = (
        settings.BASE_BACKEND_URL + "/integrations/classroom/oauth2_callback"
    )
    return flow


def get_auth_request_url():
    flow = get_flow()

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
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
    )

    # TODO `state` should also be used for better security
    return authorization_url
