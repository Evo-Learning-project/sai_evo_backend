from courses.models import UserCoursePrivilege
from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "is_teacher",
        ]

    def __init__(self, *args, **kwargs):
        context = kwargs.get("context", None)
        if self.context is not None and context.get("course") is not None:
            self.fields["course_permissions"] = serializers.SerializerMethodField()

    def get_course_permissions(self, obj):
        permissions = UserCoursePrivilege.objects.get(
            user=obj, course=self.context["course"]
        )
        return {
            "allow_privileges": permissions.allow_privileges,
            "deny_privileges": permissions.deny_privileges,
        }
