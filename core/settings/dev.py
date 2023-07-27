from .base import *

import os

# disable HTTPS requirement for oauth
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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

CSRF_TRUSTED_ORIGINS = ["http://*"]

DRF_VIEWSET_PROFILER = {
    #  "DEFAULT_OUTPUT_GENERATION_TYPE": "drf_viewset_profiler.output.FileOutput",
    "DEFAULT_OUTPUT_LOCATION": "",
    "ENABLE_SERIALIZER_PROFILER": True,
}
