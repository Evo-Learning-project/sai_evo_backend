import string
from courses.models import ExerciseTestCase
import random


def get_random_identifier(length=20):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def get_testcase_execution_block(
    testcase: ExerciseTestCase, execution_results_list_identifier: str
) -> str:
    results_dict = get_random_identifier()
    exception_identifier = get_random_identifier()
    return (
        f"try:\n"
        + f"    {testcase.code}\n"
        + f"    {results_dict} = {{'passed': True, 'id': {testcase.pk}}}\n"
        + f"except Exception as {exception_identifier}:\n"
        + f"    {results_dict} = {{'passed': False, 'id': {testcase.pk}, 'error': {exception_identifier}}}\n"
        + f"{execution_results_list_identifier}.append({results_dict})"
    )


def get_python_program_for_vm(code: str, testcases: ExerciseTestCase) -> str:
    execution_results_list_identifier = get_random_identifier()
    testcases_str = [
        get_testcase_execution_block(t, execution_results_list_identifier)
        for t in testcases
    ]
    return (
        f"{execution_results_list_identifier}=[]\n"  # declare list to hold test case results
        + f"{code}\n"  # inline submitted code
        + f"{testcases_str}\n"  # run test cases in try - except blocks
        + f"{execution_results_list_identifier}"  # print out the result list
    )
