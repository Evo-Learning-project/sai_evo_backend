from typing import List, Literal, Optional, TypedDict, Union


class TestCaseExecutionResults(TypedDict):
    id: Union[str, int]
    passed: bool
    error: Optional[str]
    stdout: Optional[str]
    stderr: Optional[str]
    # TODO add created_files, input_files


class ExecutionResults(TypedDict):
    # TODO add code: str to check the execution_results is valid for latest code
    tests: List[TestCaseExecutionResults]
    compilation_errors: Optional[str]
    execution_error: Optional[str]
    state: Literal["completed", "internal_error", "running"]
