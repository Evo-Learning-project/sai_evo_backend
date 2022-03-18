from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

REST_FRAMEWORK = {
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # "rest_framework.authentication.TokenAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",  # django-oauth-toolkit >= 1.0.0
        "rest_framework.authentication.SessionAuthentication",  # for browsable api
        "drf_social_oauth2.authentication.SocialAuthentication",
    ),
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
}

sentry_sdk.init(
    dsn="https://36f5d66ec4a44fa8965a3adfef7d289f@o1003719.ingest.sentry.io/6265953",
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)
