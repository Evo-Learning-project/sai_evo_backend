from rest_framework import serializers

from integrations.classroom.models import (
    GoogleClassroomAnnouncementTwin,
    GoogleClassroomCourseTwin,
    GoogleClassroomCourseWorkTwin,
    GoogleClassroomMaterialTwin,
)


class GoogleClassroomCourseTwinSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleClassroomCourseTwin
        fields = [
            "id",
            "enabled",
            "data",
            "remote_object_id",
            "course",
        ]
        read_only_fields = ["id", "data", "remote_object_id", "course"]


class GoogleClassroomCourseWorkTwinSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleClassroomCourseWorkTwin
        fields = ["id", "data", "remote_object_id"]
        read_only_fields = [
            "id",
            "data",
            "remote_object_id",
        ]


class GoogleClassroomMaterialTwinSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleClassroomMaterialTwin
        fields = ["id", "data", "remote_object_id"]
        read_only_fields = [
            "id",
            "data",
            "remote_object_id",
        ]


class GoogleClassroomAnnouncementTwinSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleClassroomAnnouncementTwin
        fields = ["id", "data", "remote_object_id"]
        read_only_fields = [
            "id",
            "data",
            "remote_object_id",
        ]
