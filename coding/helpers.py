import base64
import hashlib
import json
import os
import subprocess
from django.core.exceptions import ValidationError
import requests
from coding.python.runPython import get_python_program_for_vm
from courses.models import Exercise, ExerciseTestCase, ExerciseTestCaseAttachment
from courses.serializers import ExerciseTestCaseSerializer
from django.db.models.fields.files import FieldFile
from django.db.models import QuerySet
import hashlib

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


import logging

logger = logging.getLogger(__name__)


def send_jobe_request(body, headers, req_method, url=""):
    call_func = getattr(requests, req_method)
    response = call_func(
        url
        or os.environ.get(
            "JOBE_POST_RUN_URL",
            "http://192.168.1.14:4001/jobe/index.php/restapi/runs",
        ),
        data=json.dumps(body),
        headers=headers or {"content-type": "application/json"},
    )

    try:
        ret = response.json()
    except Exception:
        ret = "couldn't decode, " + str(response) + " " + str(response.content)

    return ret


"""
C
"""


def _program_stdout_matches_expected(stdout, expected_stdout):
    return stdout.rstrip("\n").rstrip(" ") == expected_stdout.rstrip("\n").rstrip(" ")


def _get_file_id_for_jobe(filename):
    return hashlib.md5(filename.encode("utf-8")).hexdigest()


def _encode_file_for_jobe(file: FieldFile) -> str:
    return base64.b64encode(file.read()).decode("utf-8")


def _create_testcase_attachments_in_jobe(testcase):
    attachments: QuerySet[ExerciseTestCaseAttachment] = testcase.attachments.all()

    for t in attachments:
        file_id = _get_file_id_for_jobe(t.attachment.name)
        file_content = _encode_file_for_jobe(t.attachment)
        response = requests.put(
            os.environ.get(
                "JOBE_FILES_URL",
                "http://192.168.1.14:4001/jobe/index.php/restapi/files/",
            )
            + str(file_id),
            data=json.dumps({"file_contents": file_content}),
            headers={"content-type": "application/json"},
        )

        if str(response.status_code)[0] != "2":
            logger.error(
                "error while creating files for test case "
                + str(testcase.pk)
                + ": jobe responded with error: "
                + str(response.status_code)
                + " ("
                + str(response.content)
                + ")\n"
                + "file id: "
                + str(file_id)
                + "file content: "
                + str(file_content)
                + "\n\n---\n\n"
            )
            response.raise_for_status()


class MissingTestCaseAttachment(Exception):
    pass


def _run_c_testcase(code, testcase):
    """
    Makes a run request to jobe to run a single test case for
    a C program
    """
    injected_files = [
        [_get_file_id_for_jobe(s.attachment.name), os.path.basename(s.attachment.name)]
        for s in testcase.attachments.all()
    ]

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
                    "parameters": {
                        "linkargs": ["-lm"],
                    },
                    "file_list": injected_files,  # attach files from test case
                }
            }
        ),
        headers={"content-type": "application/json"},
    )
    if response.status_code == 404:
        raise MissingTestCaseAttachment
    if str(response.status_code)[0] != "2":
        logger.error("jobe responded with error: " + str(response.status_code))
        response.raise_for_status()

    return response


# def _run_c_testcase_with_retry(code, testcase):
#     MAX_RETRIES = 5
#     try_n = 0

#     while try_n < MAX_RETRIES:
#         try:
#             return _run_c_testcase(code, testcase)
#         except MissingTestCaseAttachment:
#             _create_testcase_attachments_in_jobe(testcase)
#             try_n += 1

#     raise Exception


def run_c_code_in_vm(code, testcases):
    ret = {}
    for testcase in testcases:
        try:
            response = _run_c_testcase(code, testcase)
        except MissingTestCaseAttachment:
            # create missing attachments for the testcase and retry
            _create_testcase_attachments_in_jobe(testcase)
            response = _run_c_testcase(code, testcase)

        try:
            response_body = response.json()
        except Exception as e:
            # TODO better handling
            logger.error(
                "couldn't decode "
                + str(response.status_code)
                + " ("
                + str(response.content)
                + ")\n"
            )
            raise

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
                and _program_stdout_matches_expected(
                    response_body.get("stdout"), testcase.expected_stdout
                ),
                "stdout": response_body.get("stdout"),
                "stderr": response_body.get("stderr"),
                "error": JOBE_OUTCOMES[outcome_code] if outcome_code != 15 else None,
            }
        )

    return {**ret, "state": "completed"}


"""
JS/TS
"""


def run_js_code_in_vm(code, exercise, testcases, use_ts):
    """
    Takes in a string containing JS code and a list of testcases; runs the code in a JS
    virtual machine and returns the outputs given by the code in JSON format
    """

    # return JavaScriptCodeRunner(exercise, code).run()

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


"""
Python
"""


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


"""
Exposed function
"""


def get_code_execution_results(slot=None, **kwargs):
    ret = None
    exercise: Exercise = (
        slot.exercise if kwargs.get("exercise") is None else kwargs.get("exercise")
    )
    code: str = slot.answer_text if kwargs.get("code") is None else kwargs.get("code")

    testcases: QuerySet[ExerciseTestCase] = exercise.testcases.all()

    if exercise.exercise_type == Exercise.JS:
        # return run_js_code_in_vm(code, exercise, [], False)
        ret = run_js_code_in_vm(code, exercise, testcases, exercise.requires_typescript)

    elif exercise.exercise_type == Exercise.C:
        ret = run_c_code_in_vm(code, testcases)

    elif exercise.exercise_type == Exercise.PYTHON:
        ret = run_python_code_in_vm(code, testcases)

    if ret is None:
        raise ValidationError("Non-coding exercise " + str(exercise.pk))

    # add md5 of executed code to results object to keep track of what code the object refers to
    ret["code_md5"] = hashlib.md5(code.encode("utf-8")).hexdigest()
    return ret
