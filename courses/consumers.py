from decimal import Decimal
import json
from django.http import HttpRequest
from djangochannelsrestframework import permissions
from djangochannelsrestframework.observer.generics import (
    GenericAsyncAPIConsumer,
    ObserverModelInstanceMixin,
)
from djangochannelsrestframework.decorators import action
from channels.db import database_sync_to_async


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
    def __init__(self, *args, **kwargs):
        self.subscribed_instances = []
        super().__init__(*args, **kwargs)

    def lock_instance(self, pk):
        if self.check_object_permissions(pk):
            return self.queryset.get(pk=pk).lock(self.scope["user"])
        else:
            print("lock permission check failed")

    def unlock_instance(self, pk):
        if self.check_object_permissions(pk):
            return self.queryset.get(pk=pk).unlock(self.scope["user"])
        else:
            print("unlock permission check failed")

    def check_object_permissions(self, instance_pk):
        raise NotImplemented

    @action()
    async def subscribe_instance(self, request_id=None, **kwargs):
        lock = kwargs.get("lock", True)
        pk = kwargs.get("pk", None)

        try:
            if lock:
                await database_sync_to_async(self.lock_instance)(pk)

            response = await super().subscribe_instance(request_id, **kwargs)
            self.subscribed_instances.append(pk)
        except:
            await database_sync_to_async(self.unlock_instance)(pk)

        return response

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

    async def connect(self):
        # print("connect")
        return await super().connect()

    async def websocket_disconnect(self, message):
        # print("disconnect")
        for pk in self.subscribed_instances:
            await database_sync_to_async(self.unlock_instance)(pk)

        return await super().websocket_disconnect(message)


class EventConsumer(BaseObserverConsumer):
    queryset = Event.objects.all()
    model = Event
    serializer_class = serializers.EventSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def check_object_permissions(self, instance_pk):
        return True
