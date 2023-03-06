from django.contrib import admin

from integrations.models import *


@admin.register(GoogleOAuth2Credentials)
class GoogleOAuth2CredentialsAdmin(admin.ModelAdmin):
    pass
