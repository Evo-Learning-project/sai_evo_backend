from core.celery import app


import logging
from django.apps import apps
from courses.models import Course
from integrations.classroom.exceptions import UnrecoverableGoogleClassroomError

from integrations.classroom.integration import GoogleClassroomIntegration
from integrations.classroom.models import (
    GoogleClassroomIntegrationFailedTask,
)
from users.models import User
from users.serializers import UserCreationSerializer

logger = logging.getLogger(__name__)


# @app.task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_kwargs={"max_retries": 5},
#     retry_backoff=True,
#     max_retries=5,
# )
# def bulk_run_google_classroom_integration_method(
#     self, method_name, model_label, model_ids
# ):
#     """
#     Takes in the name of a method in `GoogleClassroomIntegration` and runs it for each model
#     instance, as specified by the model label and model ids.

#     The method run must take in a single argument, which is the model instance.
#     """
#     integration = GoogleClassroomIntegration()
#     method = getattr(integration, method_name)

#     model_cls = apps.get_model(model_label)
#     model_instances = model_cls.objects.filter(pk__in=model_ids)

#     for model_instance in model_instances:
#         try:
#             print("running", method_name, "for", model_instance)
#             method(model_instance)
#         except Exception as e:
#             logger.error(f"Error running {method_name} for {model_instance}: {e}")
#             raise self.retry(exc=e)


@app.task(bind=True, default_retry_delay=20, max_retries=5)
def run_google_classroom_integration_method(self, method_name, **kwargs):
    integration = GoogleClassroomIntegration()
    method = getattr(integration, method_name)

    """
    The kwargs passed for the task only contain id's of models, but the integration
    methods expect model instances - query to get actual model instances from id's
    """
    for kwarg_name, kwarg_value in kwargs.items():
        if isinstance(kwarg_value, str) and kwarg_value.startswith("model_"):
            # get rid of `model_` prefix
            suffix = kwarg_value.split("_", 1)[1]

            # kwarg is in the form `<app_label>.<model_label>_<pk>`
            # TODO what if the id contains a _? e.g. hashid
            pk = kwarg_value.split("_")[-1]
            app_model_label = suffix[: -(len(pk) + 1)]

            model_cls = apps.get_model(app_model_label)
            kwargs[kwarg_name] = model_cls.objects.get(pk=pk)

    try:
        method(**kwargs)
    except UnrecoverableGoogleClassroomError as e:
        logger.error(f"Unrecoverable error running {method_name}: {e}")
        on_unrecoverable_google_classroom_error(self.request.id, e)
        raise
    except Exception as e:
        logger.error(f"Error running {method_name}: {e}")
        raise self.retry(exc=e)


@app.task(bind=True, default_retry_delay=20, max_retries=5)
def import_enrolled_student_from_twin_course(self, course_id):
    """
    Takes the list of students enrolled in the Classroom course associated with
    the given course and creates UserCourseEnrollment objects for each student
    """
    course = Course.objects.get(id=course_id)

    # get the list of enrolled students from the Classroom course
    try:
        enrolled_students = GoogleClassroomIntegration().get_course_students(course)
    except UnrecoverableGoogleClassroomError as e:
        logger.error(
            f"Unrecoverable error running import_enrolled_student_from_twin_course: {e}"
        )
        on_unrecoverable_google_classroom_error(self.request.id, e)
        raise
    except Exception as e:
        logger.error(f"Error running import_enrolled_student_from_twin_course: {e}")
        raise self.retry(exc=e)

    enrolled_students_emails = [s["email"] for s in enrolled_students]

    # TODO refactor to factor out the logic for creating users from emails shared with `enrollments` endpoint
    # query for emails referring to existing accounts and retrieve
    # the corresponding user id's
    existing_users_by_email = User.objects.filter(
        email__in=enrolled_students_emails
    ).values_list(
        "id",
        "email",
    )

    # create User objects for each student that doesn't have an account
    emails_to_create = [
        email
        for email in enrolled_students_emails
        if email not in [e for (_, e) in existing_users_by_email]
    ]
    creation_serializer = UserCreationSerializer(
        data=[{"email": email} for email in emails_to_create], many=True
    )
    creation_serializer.is_valid(raise_exception=True)
    created_users = creation_serializer.save()

    course.enroll_users(
        [
            *(i for (i, _) in existing_users_by_email),
            *(u.id for u in created_users),
        ],
        from_integration=True,  # signal that this enrollment is from an integration
        raise_for_duplicates=False,  # just skip duplicates
    )


def on_unrecoverable_google_classroom_error(task_id, exc):
    """
    Called when a task fails due to an unrecoverable error, e.g. invalid credentials.
    For now it just creates a record in the database - in the future, we want to communicate these
    types of failures to course teachers.
    """
    GoogleClassroomIntegrationFailedTask.objects.create(
        task_id=task_id,
    )
