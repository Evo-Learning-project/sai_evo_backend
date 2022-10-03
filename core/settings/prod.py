import os

import dj_database_url

from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False

DATABASES = {
    "default": {
        **dj_database_url.parse(
            os.environ.get("DATABASE_URL", False),
            # engine="django_postgrespool2",
            conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", 60)),
        ),
        "ATOMIC_REQUESTS": True,
    }
}

MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware"] + MIDDLEWARE
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MAX_AGE = 604800 * 2  # 2 weeks

SECRET_KEY = os.environ.get("SECRET_KEY", None)

# ALLOWED_HOSTS = [
#     "*",
# ]  # * to test on DO

# force https on heroku
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
        # "file": {
        #     "level": "WARNING",
        #     "class": "logging.FileHandler",
        #     "filename": os.environ.get("LOG_FILE", "warning.log"),
        # },
    },
    "root": {
        "handlers": ["console", "mail_admins"],
        "level": os.environ.get("LOGGING_MAIL_SEVERITY", "ERROR"),
    },
    # "loggers": {
    #     "core.middleware": {
    #         "handlers": ["file"],
    #         "level": "WARNING",
    #         "propagate": True,
    #     },
    # },
}

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_HOST_USER = os.environ.get("GMAIL_APP_ADDRESS", None)
# EMAIL_HOST_PASSWORD = os.environ.get("GMAIL_APP_PWD", None)
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False


# BASE_DIR = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATIC_URL = '/static/'

# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://36f5d66ec4a44fa8965a3adfef7d289f@o1003719.ingest.sentry.io/6265953",
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.5,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "courses.consumers.ChannelLayer",
        "CONFIG": {
            "hosts": [
                os.environ.get("REDIS_URL")
                # {"address": os.environ.get("REDIS_URL")},
            ]
        },
    },
}

CSRF_TRUSTED_ORIGINS = ["https://*.di.unipi.it"]
