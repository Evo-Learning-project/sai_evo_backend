from django.contrib import admin

from integrations.classroom.models import *


@admin.register(GoogleClassroomCourseTwin)
class GoogleClassroomCourseTwinAdmin(admin.ModelAdmin):
    pass


@admin.register(GoogleClassroomCourseWorkTwin)
class GoogleClassroomCourseWorkTwinAdmin(admin.ModelAdmin):
    pass


@admin.register(GoogleClassroomAnnouncementTwin)
class GoogleClassroomAnnouncementTwinAdmin(admin.ModelAdmin):
    pass


@admin.register(GoogleClassroomMaterialTwin)
class GoogleClassroomMaterialTwinAdmin(admin.ModelAdmin):
    pass


@admin.register(GoogleClassroomEnrollmentTwin)
class GoogleClassroomEnrollmentTwinAdmin(admin.ModelAdmin):
    pass


@admin.register(GoogleClassroomCourseWorkSubmissionTwin)
class GoogleClassroomCourseWorkSubmissionTwinAdmin(admin.ModelAdmin):
    pass


@admin.register(GoogleClassroomIntegrationFailedTask)
class GoogleClassroomIntegrationFailedTaskAdmin(admin.ModelAdmin):
    pass
