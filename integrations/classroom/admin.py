from django.contrib import admin

from integrations.classroom.models import *


@admin.register(GoogleClassroomCourseTwin)
class GoogleClassroomCourseTwinAdmin(admin.ModelAdmin):
    pass
