from decimal import Decimal
import json
from django.http import HttpRequest
from djangochannelsrestframework import permissions
from djangochannelsrestframework.observer.generics import (
    GenericAsyncAPIConsumer,
    ObserverModelInstanceMixin,
)

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from courses import serializers
from courses.models import Event, Exercise

# class ExtendedAsyncJsonWsConsumer(AsyncJsonWebsocketConsumer):
#     @classmethod
#     async def encode_json(cls, content):
#         print("-----------overrIDINGGGG-----------_!!!!!!!!", content)
#         return json.dumps(content)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


class BaseObserverConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)

        # build fake request to pass user to serializer
        request = HttpRequest()
        request.user = self.scope["user"]
        context["request"] = request
        context["show_hidden_fields"] = True  #! keep an eye on this
        return context

    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content, cls=DecimalEncoder)


class EventConsumer(BaseObserverConsumer):
    queryset = Event.objects.all()
    serializer_class = serializers.EventSerializer
    permission_classes = (permissions.IsAuthenticated,)
