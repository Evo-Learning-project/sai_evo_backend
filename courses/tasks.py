import time
from coding.helpers import get_code_execution_results
from core.celery import app
from courses.models import ParticipationSubmissionSlot
from django.db import transaction

from djangochannelsrestframework import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

channel_layer = get_channel_layer()


@app.task(bind=True)
def run_js_code(self, slot_id):
    """
    Takes in the id of a submission slot, runs the js code in it, then
    saves the results to its execution_results field
    """
    from courses.consumers import SubmissionSlotConsumer

    # TODO set up retry with backoff
    slot = ParticipationSubmissionSlot.objects.get(id=slot_id)

    # run code and save outcome to slot
    results = get_code_execution_results(slot)
    slot.execution_results = results
    slot.save(update_fields=["execution_results"])

    # send completion message to consumer
    async_to_sync(channel_layer.group_send)(
        "submission_slot_" + str(slot_id),
        {"type": "task_message", "action": "execution_complete", "pk": slot_id},
    )
