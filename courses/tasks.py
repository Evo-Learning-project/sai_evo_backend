import json
import time
from coding.helpers import get_code_execution_results
from core.celery import app
from courses.models import EventParticipationSlot
from django.db import transaction

from djangochannelsrestframework import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

from celery.exceptions import MaxRetriesExceededError

import logging

logger = logging.getLogger(__name__)


@app.task(bind=True, retry_backoff=True, max_retries=5)
def run_one_off_code_task(self, exercise_id, code, task_id):
    from courses.models import Exercise

    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exception as e:
        logger.critical("Exception while getting exercise with id " + str(exercise_id))
        raise

    try:
        execution_results = get_code_execution_results(exercise=exercise, code=code)
    except Exception as e:
        logger.critical("RUN ONE-OFF CODE TASK EXCEPTION: %s", e, exc_info=1)
        try:
            self.retry(countdown=1)
        except MaxRetriesExceededError:
            execution_results = {"state": "internal_error"}

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "code_execution_task_" + task_id,
        {
            "type": "task_message",
            "task_id": task_id,
            "action": "execution_complete",
            "execution_results": json.dumps(execution_results),
        },
    )


@app.task(bind=True, retry_backoff=True, max_retries=5)
def run_participation_slot_code_task(self, slot_id):
    """
    Takes in the id of a submission slot, runs the code in it, then
    saves the results to its execution_results field
    """
    from courses.consumers import SubmissionSlotConsumer

    slot = EventParticipationSlot.objects.get(id=slot_id)
    try:
        # run code and save outcome to slot
        results = get_code_execution_results(slot=slot)
        # strip off \u0000 char
        sanitized_results = EventParticipationSlot.sanitize_json(results)
        slot.execution_results = sanitized_results
        slot.save(update_fields=["execution_results"])
    except Exception as e:
        logger.critical("RUN SLOT CODE TASK EXCEPTION: %s", e, exc_info=1)
        try:
            self.retry(countdown=1)
        except MaxRetriesExceededError:
            slot.execution_results = {"state": "internal_error"}
            slot.save(update_fields=["execution_results"])

    # TODO this can be generalized (a notify_task_complete function) to decrease coupling with Channels
    # send completion message to consumer
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "submission_slot_" + str(slot_id),
        {"type": "task_message", "action": "execution_complete", "pk": slot_id},
    )
