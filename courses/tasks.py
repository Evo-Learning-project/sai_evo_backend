import time
from coding.helpers import get_code_execution_results
from core.celery import app
from courses.models import ParticipationSubmissionSlot
from django.db import transaction

from djangochannelsrestframework import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

from celery.exceptions import MaxRetriesExceededError

import logging

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@app.task(bind=True, retry_backoff=True, max_retries=5)
def run_user_code_task(self, slot_id):
    """
    Takes in the id of a submission slot, runs the code in it, then
    saves the results to its execution_results field
    """
    from courses.consumers import SubmissionSlotConsumer

    slot = ParticipationSubmissionSlot.objects.get(id=slot_id)
    try:
        # run code and save outcome to slot
        results = get_code_execution_results(slot)
        slot.execution_results = results
        slot.save(update_fields=["execution_results"])
    except Exception as e:
        logger.critical("RUN CODE TASK EXCEPTION: %s", e, exc_info=1)
        try:
            self.retry(countdown=1)
        except MaxRetriesExceededError:
            slot.execution_results = {"state": "internal_error"}
            slot.save(update_fields=["execution_results"])

    # send completion message to consumer
    async_to_sync(channel_layer.group_send)(
        "submission_slot_" + str(slot_id),
        {"type": "task_message", "action": "execution_complete", "pk": slot_id},
    )
