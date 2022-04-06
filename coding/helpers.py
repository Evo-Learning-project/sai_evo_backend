import json
import os
import subprocess
from django.core.exceptions import ValidationError

from courses.models import Exercise, ParticipationSubmissionSlot
from courses.serializers import ExerciseTestCaseSerializer


def run_code_in_vm(code, testcases, use_ts):
    """
    Takes in a string containing JS code and a list of testcases; runs the code in a JS
    virtual machine and returns the outputs given by the code in JSON format
    """

    node_vm_path = os.environ.get("NODE_VM_PATH", "coding/runJs.js")

    testcases_json = [{"id": t.id, "assertion": t.code} for t in testcases]

    # call node subprocess and run user code against test cases
    res = subprocess.check_output(
        [
            "node",
            node_vm_path,
            code,
            json.dumps(testcases_json),
            json.dumps(use_ts),
        ]
    )
    return {**json.loads(res), "state": "completed"}


def get_code_execution_results(slot: ParticipationSubmissionSlot):
    if slot.exercise.exercise_type != Exercise.JS:
        raise ValidationError("Non-JS exercise " + slot.exercise.pk)

    testcases = slot.exercise.testcases.all()

    return run_code_in_vm(
        slot.answer_text, testcases, slot.exercise.requires_typescript
    )
