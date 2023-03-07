from rest_framework import serializers

from integrations.classroom.models import GoogleClassroomCourseTwin


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
