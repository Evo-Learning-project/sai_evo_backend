from typing import Callable, Iterable, Type

import logging
from django.db import models

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    def run_integration_method_as_task(self, task, method_name, **kwargs):
        """
        Celery tasks cannot be passed model instances directly, but the methods that are wrapped
        inside of the tasks do accept model instances. So we turn the kwargs containing model
        instances into kwargs containing the model's pk, and the task will re-query for the models
        """
        for kwarg_name, kwarg_value in kwargs.items():
            if isinstance(kwarg_value, models.Model):
                model_label = (
                    f"{kwarg_value._meta.app_label}.{kwarg_value._meta.model_name}"
                )
                kwargs[kwarg_name] = f"model_{model_label}_{kwarg_value.pk}"

        task.delay(method_name, **kwargs)

    def get_task(self, integration_cls):
        from integrations.classroom.tasks import run_google_classroom_integration_method

        return run_google_classroom_integration_method

    def dispatch(self, action_name: str, course: "Course", **kwargs):
        integrations = self.get_enabled_integrations_for(course)

        # loop over all the integrations enabled for the given course, and
        # for each of them, if the dispatched action is supported, schedule
        # the corresponding handler to be run with the given arguments
        for integration_cls in integrations:
            integration = integration_cls()
            # check the current integration supports the dispatched action
            if action_name in integration.get_available_actions():
                method_name = integration_cls.ACTION_HANDLER_PREFIX + action_name
                task = self.get_task(integration_cls)
                self.run_integration_method_as_task(task, method_name, **kwargs)
            else:
                logger.warning(
                    f"{str(integration_cls)} doesn't support action {action_name}"
                )

    def get_enabled_integrations_for(
        self,
        course: "Course",
    ) -> Iterable[Type["BaseEvoIntegration"]]:
        """
        Returns a list of subclasses of `BaseEvoIntegration` representing integrations
        enabled for the given course.
        """
        from integrations.classroom.models import GoogleClassroomCourseTwin
        from integrations.classroom.integration import GoogleClassroomIntegration

        ret = []

        # NOTE currently, the only integration available is the Google Classroom one, so
        # this is hard coded. in the future, we may dynamically load available integrations
        # TODO this potentially causes a lot of queries - find a way that exploits prefetching
        if GoogleClassroomCourseTwin.objects.filter(course=course).exists():
            ret.append(GoogleClassroomIntegration)

        return ret
