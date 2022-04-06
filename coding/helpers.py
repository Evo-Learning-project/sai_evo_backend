import json
import os
import subprocess
from django.core.exceptions import ValidationError
import requests
from courses.models import Exercise, ParticipationSubmissionSlot
from courses.serializers import ExerciseTestCaseSerializer


def program_stdout_matches_expected(stdout, expected_stdout):
    return stdout == expected_stdout


def run_c_code_in_vm(code, testcases):
    outcomes = {
        11: "compilation_error",
        12: "runtime_error",
        13: "timeout",
        15: "ok",
        17: "memory_limit_exceeded",
        19: "illegal_system_call",
        20: "internal_error",
        21: "overload",
    }
    ret = {}
    for testcase in testcases:
        response = requests.post(
            os.environ.get(
                "JOBE_POST_RUN_URL",
                "http://192.168.1.14:4001/jobe/index.php/restapi/runs",
            ),
            data=json.dumps(
                {
                    "run_spec": {
                        "language_id": "c",
                        "input": testcase.stdin,
                        "sourcecode": code,  #'\n#include <stdio.h>\n\nint main() {\n    printf("Hello world\\n");\n}\n',
                    }
                }
            ),
            headers={"content-type": "application/json"},
        )
        # print("RESPONSE", response, response.json())
        response_body = response.json()
        outcome_code = response_body["outcome"]
        if outcome_code == 11:
            return {"compilation_errors": response_body["cmpinfo"]}
        if "tests" not in ret:
            # initialize
            ret["tests"] = []
        if outcome_code == 15:
            ret["tests"].append(
                {
                    "id": testcase.id,
                    "passed": "stdout" in response_body
                    and program_stdout_matches_expected(
                        response_body["stdout"], testcase.expected_stdout
                    ),
                    "stdout": response_body["stdout"],
                }
            )
        else:  # some error happened; append test case info
            ret["tests"].append(
                {"id": testcase.id, "error": outcomes[outcome_code], "passed": False}
            )
    return ret


def run_js_code_in_vm(code, testcases, use_ts):
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
    testcases = slot.exercise.testcases.all()

    if slot.exercise.exercise_type == Exercise.JS:
        return run_js_code_in_vm(
            slot.answer_text, testcases, slot.exercise.requires_typescript
        )

    if slot.exercise.exercise_type == Exercise.C:
        return run_c_code_in_vm(slot.answer_text, testcases)

    raise ValidationError("Non-coding exercise " + slot.exercise.pk)
