import json
import os
import subprocess
from django.core.exceptions import ValidationError
import requests
from coding.python.runPython import get_python_program_for_vm
from courses.models import Exercise
from courses.serializers import ExerciseTestCaseSerializer

JOBE_OUTCOMES = {
    11: "compilation_error",
    12: "runtime_error",
    13: "timeout",
    15: "ok",
    17: "memory_limit_exceeded",
    19: "illegal_system_call",
    20: "internal_error",
    21: "overload",
}


def program_stdout_matches_expected(stdout, expected_stdout):
    return stdout.rstrip("\n").rstrip(" ") == expected_stdout.rstrip("\n").rstrip(" ")


def run_python_code_in_vm(code, testcases):
    code_to_run = get_python_program_for_vm(code, testcases)
    print("CODE TO RUN\n", code_to_run)
    response = requests.post(
        os.environ.get(
            "JOBE_POST_RUN_URL",
            "http://192.168.1.14:4001/jobe/index.php/restapi/runs",
        ),
        data=json.dumps(
            {
                "run_spec": {
                    "language_id": "python3",
                    # "input": testcase.stdin,
                    "sourcecode": code_to_run,
                    # "parameters": {"linkargs": ["-lm"]},
                }
            }
        ),
        headers={"content-type": "application/json"},
    )
    print("RESPONSE", response)
    response_body = response.json()
    outcome_code = response_body["outcome"]

    # compilation errors
    if outcome_code == 11:
        return {
            "compilation_errors": response_body["cmpinfo"],
            "state": "completed",
        }

    print("RES BODY", response_body, "OUTCOME CODE", outcome_code)

    results = {}
    if response_body["stdout"]:
        results["tests"] = json.loads(response_body["stdout"])

    if response_body["stderr"]:
        results["execution_error"] = response_body["stderr"]

    return {**results, "state": "completed"}


def run_c_code_in_vm(code, testcases):
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
                        "parameters": {"linkargs": ["-lm"]},
                    }
                }
            ),
            headers={"content-type": "application/json"},
        )
        response_body = response.json()
        outcome_code = response_body["outcome"]
        # compilation errors
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
                "error": JOBE_OUTCOMES[outcome_code] if outcome_code != 15 else None,
            }
        )

    return {**ret, "state": "completed"}


def run_js_code_in_vm(code, testcases, use_ts):
    """
    Takes in a string containing JS code and a list of testcases; runs the code in a JS
    virtual machine and returns the outputs given by the code in JSON format
    """

    node_vm_path = os.environ.get("NODE_VM_PATH", "coding/ts/runJs.js")

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

    if exercise.exercise_type == Exercise.PYTHON:
        return run_python_code_in_vm(code, testcases)

    raise ValidationError("Non-coding exercise " + str(exercise.pk))
