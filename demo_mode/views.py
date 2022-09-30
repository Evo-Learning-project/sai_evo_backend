from django.db import IntegrityError
from rest_framework import filters, mixins, status, viewsets
from rest_access_policy import AccessPolicy
import os
from rest_framework import serializers
from demo_mode.models import DemoInvitation
from rest_framework.response import Response
from social_core.backends.google import GoogleOAuth2

import logging

logger = logging.getLogger(__name__)


class DemoInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoInvitation
        fields = [
            "id",
            "main_invitee_email",
            "other_invitees_emails",
            "duration_hours",
        ]
        read_only_fields = ["main_invitee_email", "duration_hours"]


class DemoInvitationPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": ["*"],
            "effect": "allow",
            # "condition": "token_is_present",
        },
        {
            "action": ["create"],
            "principal": ["*"],
            "effect": "allow",
            # "condition": "token_is_present",
        },
    ]

    # def token_is_present(self, request, view, action):
    #     # return True
    #     request_token = request.data.get("DEMO_TOKEN", "")
    #     secret_token = os.environ["DEMO_TOKEN"]

    #     return request_token == secret_token


class DemoInvitationViewSet(
    # viewsets.ModelViewSet
    mixins.ListModelMixin,
    # # mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    # # mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = DemoInvitation.objects.all()
    permission_classes = [DemoInvitationPolicy]
    serializer_class = DemoInvitationSerializer

    def create(self, request, *args, **kwargs):
        try:
            token = request.data["token"]
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            user_profile = GoogleOAuth2().user_data(access_token=token)
        except Exception as e:
            logger.error(
                "An error occurred while trying to fetch user data from Google: "
                + str(e)
            )
            if hasattr(e, "response") and e.response.status_code == 401:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        email = user_profile["email"]
        self.email = email

        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def perform_create(self, serializer) -> None:
        serializer.save(main_invitee_email=self.email)
