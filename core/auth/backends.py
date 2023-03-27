from social_core.backends.google import GoogleOAuth2
from google_auth_oauthlib.flow import Flow

from integrations.classroom.auth import get_flow

import os

from integrations.models import GoogleOAuth2Credentials


class GoogleOAuth2Backend(GoogleOAuth2):
    def do_auth(self, access_token, *args, **kwargs):
        code = self.data.get("code")
        """
            An authorization code was provided - use it to fetch a pair of
            access and refresh tokens, store them, and complete normal
            authentication flow
            https://developers.google.com/identity/protocols/oauth2/web-server#exchange-authorization-code
        """
        if code is not None:
            flow = Flow.from_client_config(
                {
                    "installed": {
                        "client_id": os.environ.get("GOOGLE_INTEGRATION_CLIENT_ID"),
                        "project_id": os.environ.get("GOOGLE_INTEGRATION_PROJECT_ID"),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_secret": os.environ.get(
                            "GOOGLE_INTEGRATION_CLIENT_SECRET"
                        ),
                    }
                },
                redirect_uri=os.environ.get("BASE_FRONTEND_URL"),
                scopes=None,
            )
            response = flow.fetch_token(code=code)
            access_token = response["access_token"]

            # now that we've obtained an access token, complete normal flow
            user = super().do_auth(access_token, *args, **kwargs)
            # store user's credentials for offline use
            GoogleOAuth2Credentials.create_from_auth_response(user, response)
        else:
            user = super().do_auth(access_token, *args, **kwargs)

        return user

    def auth_allowed(self, response, details):
        """Return True if the user should be allowed to authenticate"""
        emails = [email.lower() for email in self.setting("WHITELISTED_EMAILS", [])]
        domains = [domain.lower() for domain in self.setting("WHITELISTED_DOMAINS", [])]
        email = details.get("email")
        if email and (emails or domains):
            email = email.lower()
            domain = email.split("@", 1)[1]

            if email in emails:
                return True

            for allowed_domain in domains:
                allowed_domain_suffix = allowed_domain.split("*.")[-1]
                if allowed_domain_suffix in domain:
                    return True
            return False
        return True
