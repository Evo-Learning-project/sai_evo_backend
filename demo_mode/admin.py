from django.contrib import admin

from .models import *


@admin.register(DemoInvitation)
class DemoInvitationAdmin(admin.ModelAdmin):
    pass
