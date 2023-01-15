from social_core.backends.google import GoogleOAuth2


class GoogleOAuth2Backend(GoogleOAuth2):
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
