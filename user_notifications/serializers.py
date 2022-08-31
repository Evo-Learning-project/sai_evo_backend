from rest_framework.serializers import ModelSerializer, RelatedField
from rest_framework import serializers
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType
from gamification.notifications import NOTIFICATION_SERIALIZER_GENERIC_RELATION_MAPPING
from users.models import User
from users.serializers import UserSerializer


def get_generic_relations_mapping():
    return NOTIFICATION_SERIALIZER_GENERIC_RELATION_MAPPING


class ContentTypeSerializer(ModelSerializer):
    class Meta:
        model = ContentType
        fields = ["app_label", "model"]


class GenericRelatedField(RelatedField):
    def __init__(self, *args, **kwargs):
        self.related_serializers_mapping = kwargs.pop("mapping", {})
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        for cls, serializer_cls in self.related_serializers_mapping.items():
            if isinstance(value, cls):
                serializer = serializer_cls(value)
                return serializer.data

        assert False, "GenericNotificationRelatedField: value is " + str(value)


class NotificationSerializer(ModelSerializer):
    recipient = UserSerializer()
    actor = UserSerializer()
    verb = serializers.CharField()
    level = serializers.CharField()
    description = serializers.CharField()
    timestamp = serializers.DateTimeField(read_only=True)
    unread = serializers.BooleanField()
    public = serializers.BooleanField()
    deleted = serializers.BooleanField()
    emailed = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "actor",
            # "target",
            "verb",
            "level",
            "description",
            "unread",
            "public",
            "deleted",
            "emailed",
            "timestamp",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # instantiate generic related fields
        related_serializers_mapping = kwargs.get(
            "generic_relations_mapping", get_generic_relations_mapping()
        )
        self.fields["target"] = GenericRelatedField(
            mapping=related_serializers_mapping, read_only=True
        )
        self.fields["action_object"] = GenericRelatedField(
            mapping=related_serializers_mapping, read_only=True
        )

    def create(self, validated_data):
        recipient_data = validated_data.pop("recipient")
        recipient = User.objects.get_or_create(id=recipient_data["id"])
        actor_data = validated_data.pop("actor")
        actor = User.objects.get_or_create(id=actor_data["id"])
        notification = Notification.objects.create(
            recipient=recipient[0], actor=actor[0], **validated_data
        )
        return notification
