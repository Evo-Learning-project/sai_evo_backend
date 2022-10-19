from abc import ABC, abstractmethod
import os
import subprocess
import json
from typing import Any, Dict, Iterable
from coding.execution_results import ExecutionResults, TestCaseExecutionResults
from coding.templates.compiler import ProgrammingExerciseTemplateCompiler
from courses.models import Exercise, ExerciseTestCase
import requests


class CodeRunner(ABC):
    def __init__(
        self, exercise: Exercise, code: str, one_testcase_at_a_time: bool = False
    ) -> None:
        self.exercise = exercise
        self.code = code
        self.template_compiler = ProgrammingExerciseTemplateCompiler(exercise, code)
        self.one_testcase_at_a_time = one_testcase_at_a_time

    @abstractmethod
    def compile(self):
        ...

    @abstractmethod
    def run_testcase(self, testcase: ExerciseTestCase) -> TestCaseExecutionResults:
        ...

    @abstractmethod
    def run_all_testcases(self) -> Iterable[TestCaseExecutionResults]:
        ...

    # TODO define interface for return type
    def run(self) -> ExecutionResults:
        if self.one_testcase_at_a_time:
            execution_results = {"tests": []}
            for testcase in self.exercise.testcases.all():
                try:
                    testcase_execution_results = self.run_testcase(testcase)
                    execution_results["tests"].append(testcase_execution_results)
                except Exception:  # TODO handle error
                    execution_results["error"] = "abc"
                    break
        else:
            execution_results = self.run_all_testcases()

        return execution_results


class JobeSandBoxCodeRunner(CodeRunner):
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

    JOBE_OK = 15
    JOBE_COMPILATION_ERROR = 11

    def compile(self):
        pass

    @abstractmethod
    def get_run_spec_parameters(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def get_language_code(self) -> str:
        ...

    def run_testcase(self, testcase: ExerciseTestCase):
        # TODO ensure files exist for testcase files - handle relevant response error

        response = requests.post(
            os.environ.get(
                "JOBE_POST_RUN_URL",
                "http://192.168.1.14:4001/jobe/index.php/restapi/runs",
            ),
            data=json.dumps(
                {
                    "run_spec": {
                        "language_id": self.get_language_code(),  # "c",
                        # TODO handle file testcases here
                        "input": testcase.stdin,
                        "sourcecode": self.code,
                        "parameters": self.get_run_spec_parameters(),
                        # "file_list": [["555555555", "file1"]]
                    }
                }
            ),
            headers={"content-type": "application/json"},
        )
        response_body = response.json()
        outcome_code = response_body["outcome"]

        if outcome_code == self.JOBE_COMPILATION_ERROR:
            # TODO raise an error that will stop the outer loop
            return {
                "compilation_errors": response_body["cmpinfo"],
                "state": "completed",
            }

        return {
            "id": testcase.id,
            "passed": outcome_code == self.JOBE_OK
            and program_stdout_matches_expected(
                response_body.get("stdout"), testcase.expected_stdout
            ),
            "stdout": response_body.get("stdout"),
            "stderr": response_body.get("stderr"),
            "error": self.JOBE_OUTCOMES[outcome_code]
            if outcome_code != self.JOBE_OK
            else None,
        }

    def run_all_testcases(self):
        return NotImplemented


class CCodeRunner(JobeSandBoxCodeRunner):
    def __init__(
        self, exercise: Exercise, code: str, one_testcase_at_a_time: bool = False
    ) -> None:
        one_testcase_at_a_time = True
        super().__init__(exercise, code, one_testcase_at_a_time)

    def get_language_code(self) -> str:
        return "c"

    def get_run_spec_parameters(self) -> Dict[str, Any]:
        # link the commonly used math module
        return {"linkargs": ["-lm"]}


class NodeSandboxTypeScriptCodeRunner(CodeRunner):
    def run_all_testcases(self) -> ExecutionResults:
        # TODO implement
        pass

    def run_testcase(self, testcase: ExerciseTestCase) -> TestCaseExecutionResults:
        # TODO implement
        return NotImplemented


# class NodeSandboxJavaScriptCodeRunner(CodeRunner):
#     def compile(self):
#         pass


class JavaScriptCodeRunner(CodeRunner):
    NODE_VM_PATH = os.environ.get("NODE_VM_PATH", "coding/ts/runTemplate.js")

    def run(self):
        # call node subprocess and run user code against test cases
        try:
            res = subprocess.check_output(
                [
                    "node",
                    self.NODE_VM_PATH,
                    self.template_compiler.get_template(),
                    # inject JS-specific identifiers
                    json.dumps(
                        self.template_compiler.language_specific_template_context
                    ),
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
