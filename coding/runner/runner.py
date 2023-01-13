# from abc import ABC, abstractmethod
# import os
# import subprocess
# import json
# from coding.templates.compiler import ProgrammingExerciseTemplateCompiler
# from courses.models import Exercise


# class CodeRunner(ABC):
#     def __init__(self, exercise: Exercise, code: str) -> None:
#         self.exercise = exercise
#         self.code = code
#         self.template_compiler = ProgrammingExerciseTemplateCompiler(exercise, code)

#     @abstractmethod
#     def run(self):
#         pass


# class JavaScriptCodeRunner(CodeRunner):
#     NODE_VM_PATH = os.environ.get("NODE_VM_PATH", "coding/ts/runTemplate.js")

#     def run(self):
#         # call node subprocess and run user code against test cases
#         try:
#             res = subprocess.check_output(
#                 [
#                     "node",
#                     self.NODE_VM_PATH,
#                     self.template_compiler.get_template(),
#                     # inject JS-specific identifiers
#                     json.dumps(
#                         self.template_compiler.language_specific_template_context
#                     ),
#                 ]
#             )
#             return {**json.loads(res), "state": "completed"}
#         except subprocess.CalledProcessError as e:
#             print(
#                 "-----\n\n\n",
#                 e.returncode,
#                 "\n\n",
#                 e.output,
#                 "\n\n",
#                 e.stdout,
#                 "\n\n",
#                 e.cmd,
#                 "\n\n",
#                 e.args,
#                 "\n\n-----",
#             )
