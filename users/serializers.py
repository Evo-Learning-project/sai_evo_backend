from courses.logic.privileges import get_user_privileges
from rest_framework import serializers

from users.models import User


class UserCreationSerializer(serializers.ModelSerializer):
    """
    A write-only serializer to create a user from an email address.
    It's used in certain views, such as the one to set user permissions, to
    preemptively create user accounts to assign certain relationships.
    """

    class Meta:
        model = User
        fields = ["email"]

    def create(self, validated_data):
        # set username to hold the same value as email
        validated_data["username"] = validated_data["email"]
        return super().create(validated_data)


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
            "avatar_url",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context is not None and self.context.get("course") is not None:
            self.fields["course_privileges"] = serializers.SerializerMethodField()

    def get_course_privileges(self, obj):
        # !!
        return get_user_privileges(obj, self.context["course"])
