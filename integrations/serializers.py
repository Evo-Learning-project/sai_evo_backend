from integrations.const import OPTIONAL_INTEGRATION_EVENT_QUERY_PARAM
from rest_framework import serializers

from integrations.mixins import IntegrationModelMixin


class IntegrationModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer for a model that inherits from IntegrationModelMixin.
    Allows query params in the request relating to integration  actions to be
    passed to the model instance as fields before saving.
    """

    def update(self, instance, validated_data):
        fire_event_param = self.context["request"].query_params.get(
            OPTIONAL_INTEGRATION_EVENT_QUERY_PARAM, "False"
        )
        should_fire_event = fire_event_param.lower() in ("true", "1", "yes")
        is_integration_model = isinstance(instance, IntegrationModelMixin)
        if is_integration_model:
            setattr(instance, instance.FIRE_INTEGRATION_EVENT, should_fire_event)
        return super().update(instance, validated_data)
