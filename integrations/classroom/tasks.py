from core.celery import app

from celery.exceptions import MaxRetriesExceededError

import logging
from django.apps import apps

from integrations.classroom.integration import GoogleClassroomIntegration

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=True,
    max_retries=5,
)
def run_google_classroom_integration_method(self, method_name, **kwargs):
    integration = GoogleClassroomIntegration()
    method = getattr(integration, method_name)

    print("-----\n\n", kwargs, "\n\n----")

    """
    The kwargs passed for the task only contain id's of models, but the integration
    methods expect model instances - query to get actual model instances from id's
    """
    for kwarg_name, kwarg_value in kwargs.items():
        if isinstance(kwarg_value, str) and kwarg_value.startswith("model_"):
            # get rid of `model_` prefix
            suffix = kwarg_value.split("_", 1)[1]

            # kwarg is in the form `<app_label>.<model_label>_<pk>`
            pk = kwarg_value.split("_")[-1]
            app_model_label = suffix[: -(len(pk) + 1)]

            model_cls = apps.get_model(app_model_label)
            kwargs[kwarg_name] = model_cls.objects.get(pk=pk)

    method(**kwargs)
