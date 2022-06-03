from decimal import Decimal
import json
import random
from django.http import HttpRequest
from djangochannelsrestframework import permissions
from djangochannelsrestframework.observer.generics import (
    GenericAsyncAPIConsumer,
    ObserverModelInstanceMixin,
)
from djangochannelsrestframework.decorators import action
from channels.db import database_sync_to_async

from rest_framework.exceptions import PermissionDenied
import msgpack

from django.core.exceptions import ObjectDoesNotExist


from django.db.models import Model

from channels.generic.websocket import (
    AsyncJsonWebsocketConsumer,
    AsyncWebsocketConsumer,
)

from courses import serializers
from courses.logic.privileges import (
    MANAGE_EVENTS,
    MANAGE_EXERCISES,
    UPDATE_COURSE,
    check_privilege,
)
from courses.models import (
    Event,
    EventParticipationSlot,
    Exercise,
)

from hashid_field import Hashid

from channels_redis.core import RedisChannelLayer


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Hashid):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class ChannelLayer(RedisChannelLayer):
    def serialize(self, message):
        value = msgpack.packb(
            message, default=CustomEncoder().default, use_bin_type=True
        )
        if self.crypter:
            value = self.crypter.encrypt(value)

        # As we use an sorted set to expire messages
        # we need to guarantee uniqueness, with 12 bytes.
        random_prefix = random.getrandbits(8 * 12).to_bytes(12, "big")
        return random_prefix + value


class BaseObserverConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    LOCK_BY_DEFAULT = True

    def __init__(self, *args, **kwargs):
        self.subscribed_instances = []
        self.locked_instances = []
        super().__init__(*args, **kwargs)

    def lock_instance(self, pk):
        return self.queryset.get(pk=pk).lock(self.scope["user"])

    def unlock_instance_or_give_up(self, pk):
        # unlocks an instance that the user has a lock on or removes the user
        # from its waiting queue if the lock hadn't been acquired yet
        return self.queryset.get(pk=pk).unlock(self.scope["user"])

    @action()
    async def subscribe_instance(self, request_id=None, **kwargs):
        lock = kwargs.get("lock", self.LOCK_BY_DEFAULT)
        pk = kwargs.get("pk", None)

        try:
            if lock:
                await database_sync_to_async(self.lock_instance)(pk)
                self.locked_instances.append(pk)

            response = await super().subscribe_instance(request_id, **kwargs)
            self.subscribed_instances.append(pk)
        except:
            await database_sync_to_async(self.unlock_instance_or_give_up)(pk)

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
        return json.dumps(content, cls=CustomEncoder)

    async def websocket_disconnect(self, message):
        for pk in self.locked_instances:
            await database_sync_to_async(self.unlock_instance_or_give_up)(pk)

        return await super().websocket_disconnect(message)


class EventConsumer(BaseObserverConsumer):
    queryset = Event.objects.all()
    serializer_class = serializers.EventSerializer
    permission_classes = (permissions.IsAuthenticated,)

    async def check_permissions(self, action, **kwargs):
        if action == "subscribe_instance":
            try:
                obj = await database_sync_to_async(
                    self.queryset.select_related("course").get
                )(pk=kwargs["pk"])
            except ObjectDoesNotExist:
                return False
            if not await database_sync_to_async(check_privilege)(
                self.scope["user"], obj.course.pk, MANAGE_EVENTS
            ):
                raise PermissionDenied()
        return await super().check_permissions(action, **kwargs)


class ExerciseConsumer(BaseObserverConsumer):
    queryset = Exercise.objects.all()
    serializer_class = serializers.ExerciseSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # .
    async def check_permissions(self, action, **kwargs):
        if action == "subscribe_instance":
            try:
                obj = await database_sync_to_async(
                    self.queryset.select_related("course").get
                )(pk=kwargs["pk"])
            except ObjectDoesNotExist:
                raise PermissionDenied()
            if not await database_sync_to_async(check_privilege)(
                self.scope["user"], obj.course.pk, MANAGE_EXERCISES
            ):
                raise PermissionDenied()
        return await super().check_permissions(action, **kwargs)


class SubmissionSlotConsumer(AsyncWebsocketConsumer):
    queryset = EventParticipationSlot.objects.all()

    async def receive(self, text_data=None, bytes_data=None):
        payload = json.loads(text_data)
        if "action" in payload and payload["action"] == "subscribe_instance":
            await self.subscribe_instance(payload.get("pk"))
        else:
            print("unknown message", text_data)

    async def task_message(self, payload):
        if payload["action"] == "execution_complete":
            slot = await database_sync_to_async(self.queryset.get)(pk=payload["pk"])
            await self.channel_layer.group_send(
                "submission_slot_" + str(payload["pk"]),
                {
                    "type": "execution.results",
                    "payload": slot.execution_results,
                },
            )
        else:
            print("unknown action", payload)

    async def subscribe_instance(self, pk):
        if pk is not None and await self.check_permissions(pk=pk):
            await self.channel_layer.group_add(
                "submission_slot_" + str(pk), self.channel_name
            )
            print("subscribed", "submission_slot_" + str(pk))

    async def check_permissions(self, **kwargs):
        try:
            obj = await database_sync_to_async(
                self.queryset.select_related("participation__user").get
            )(pk=kwargs["pk"])
        except ObjectDoesNotExist:
            return False
        if obj.participation.user != self.scope["user"]:
            return False
        return True

    async def execution_results(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "action": "execution_results",
                    "data": event["payload"],
                }
            )
        )
