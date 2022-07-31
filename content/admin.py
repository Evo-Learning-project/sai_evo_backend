from content.models import *
from django.contrib import admin


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    pass
