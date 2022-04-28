import json
import os
import subprocess
from django.core.exceptions import ValidationError
import requests
from courses.models import Exercise, ParticipationSubmissionSlot
from courses.serializers import ExerciseTestCaseSerializer


def program_stdout_matches_expected(stdout, expected_stdout):
    return stdout.rstrip("\n").rstrip(" ") == expected_stdout.rstrip("\n").rstrip(" ")


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
                        "sourcecode": code,
                    }
                }
            ),
            headers={"content-type": "application/json"},
        )
        response_body = response.json()
        outcome_code = response_body["outcome"]
        if outcome_code == 11:
            return {
                "compilation_errors": response_body["cmpinfo"],
                "state": "completed",
            }
        if "tests" not in ret:
            # initialize test case list
            ret["tests"] = []

        ret["tests"].append(
            {
                "id": testcase.id,
                "passed": outcome_code == 15
                and program_stdout_matches_expected(
                    response_body.get("stdout"), testcase.expected_stdout
                ),
                "stdout": response_body.get("stdout"),
                "stderr": response_body.get("stderr"),
                "error": outcomes[outcome_code] if outcome_code != 15 else None,
            }
        )

    return {**ret, "state": "completed"}


def run_js_code_in_vm(code, testcases, use_ts):
    """
    Takes in a string containing JS code and a list of testcases; runs the code in a JS
    virtual machine and returns the outputs given by the code in JSON format
    """

    node_vm_path = os.environ.get("NODE_VM_PATH", "coding/runJs.js")

    testcases_json = [{"id": t.id, "assertion": t.code} for t in testcases]

    # call node subprocess and run user code against test cases
    try:
        res = subprocess.check_output(
            [
                "node",
                node_vm_path,
                code,
                json.dumps(testcases_json),
                json.dumps(use_ts),
            ]
        )
        print("RES", res)
        return {**json.loads(res), "state": "completed"}
    except subprocess.CalledProcessError as e:
        print(
            "-----\n\n\n",
            e.returncode,
            "\n\n",
            e.output,
            "\n\n",
            e.stdout,
            "\n\n",
            e.cmd,
            "\n\n",
            e.args,
            "\n\n-----",
        )


def get_code_execution_results(slot=None, **kwargs):
    exercise = (
        slot.exercise if kwargs.get("exercise") is None else kwargs.get("exercise")
    )
    code = slot.answer_text if kwargs.get("code") is None else kwargs.get("code")

    testcases = exercise.testcases.all()

    if exercise.exercise_type == Exercise.JS:
        return run_js_code_in_vm(code, testcases, exercise.requires_typescript)

    if exercise.exercise_type == Exercise.C:
        return run_c_code_in_vm(code, testcases)

    raise ValidationError("Non-coding exercise " + str(exercise.pk))
