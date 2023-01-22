from courses.logic.privileges import get_user_privileges
from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "is_teacher",
            "mat",
            "course",
            "avatar_url",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "is_teacher",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context is not None and self.context.get("course") is not None:
            self.fields["course_privileges"] = serializers.SerializerMethodField()

    def get_course_privileges(self, obj):
        # !!
        return get_user_privileges(obj, self.context["course"])
