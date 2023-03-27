from social_core.backends.google import GoogleOAuth2
from google_auth_oauthlib.flow import Flow

from integrations.classroom.auth import get_flow


class GoogleOAuth2Backend(GoogleOAuth2):
    def do_auth(self, access_token, *args, **kwargs):
        from integrations.classroom.integration import GoogleClassroomIntegration

        code = self.data.get("code")
        if code is not None:
            config = GoogleClassroomIntegration().get_client_config()

            flow = get_flow()
            # Flow.from_client_config(
            #     config, scopes=GoogleClassroomIntegration.SCOPES
            # )
            access_token = flow.fetch_token(
                code=code,
                # client_id=config["installed"]["client_id"],
                # client_secret=config["installed"]["client_secret"],
            )

        # credentials = flow.credentials
        return super().do_auth(access_token, *args, **kwargs)

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
