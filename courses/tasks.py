import time
from coding.helpers import get_code_execution_results
from core.celery import app
from courses.models import ParticipationSubmissionSlot


@app.task(bind=True)
def run_js_code(self, slot_id):
    """
    Takes in the id of a submission slot, runs the js code in it, then
    saves the results to its execution_results field
    """
    print("running js code for slot", slot_id)
    slot = ParticipationSubmissionSlot.objects.get(id=slot_id)
    results = get_code_execution_results(slot)
    print("slot", slot_id, "results", results)
    time.sleep(1)
    slot.execution_results = results
    time.sleep(1)
    slot.save()
    time.sleep(1)
    print("slot", slot_id, "saved")
