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

from rest_framework.exceptions import PermissionDenied


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
from courses.models import Event, Exercise, ParticipationSubmissionSlot


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


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

    async def handle_observed_action(self, action, group=None, **kwargs):
        print("HANDLE")
        return await super().handle_observed_action(action, group, **kwargs)

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
        return json.dumps(content, cls=DecimalEncoder)

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
            except Model.DoesNotExist:
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

    async def check_permissions(self, action, **kwargs):
        if action == "subscribe_instance":
            try:
                obj = await database_sync_to_async(
                    self.queryset.select_related("course").get
                )(pk=kwargs["pk"])
            except Model.DoesNotExist:
                return False
            if not await database_sync_to_async(check_privilege)(
                self.scope["user"], obj.course.pk, MANAGE_EXERCISES
            ):
                raise PermissionDenied()
        return await super().check_permissions(action, **kwargs)


class SubmissionSlotConsumer(
    AsyncWebsocketConsumer
    # BaseObserverConsumer
):
    LOCK_BY_DEFAULT = False
    queryset = ParticipationSubmissionSlot.objects.all()
    serializer_class = serializers.ParticipationSubmissionSlotSerializer
    permission_classes = (permissions.IsAuthenticated,)

    # async def connect(self):
    #     await self.channel_layer.group_add("submission_slot", self.channel_name)
    #     await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        payload = json.loads(text_data)
        if "action" in payload and payload["action"] == "subscribe_instance":
            await self.subscribe_instance(payload.get("pk"))
        else:
            print("unknown message", text_data)

    async def task_message(self, event):
        print("TASK MESSAGE-------------", event)

    async def subscribe_instance(self, pk):
        if pk is not None:
            await self.channel_layer.group_add(
                "submission_slot_" + str(pk), self.channel_name
            )
            print("subscribed", "submission_slot_" + str(pk))

    # async def check_permissions(self, action, **kwargs):
    #     if action == "subscribe_instance":
    #         try:
    #             obj = await database_sync_to_async(
    #                 self.queryset.select_related("submission__participation__user").get
    #             )(pk=kwargs["pk"])
    #         except Model.DoesNotExist:
    #             return False
    #         print("USER", obj.submission.participation.user)
    #         if obj.submission.participation.user != self.scope["user"]:
    #             raise PermissionDenied()
    #     return await super().check_permissions(action, **kwargs)
