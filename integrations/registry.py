from typing import Callable, Iterable, Type
from courses.models import Course
from integrations.classroom.integration import GoogleClassroomIntegration
from integrations.integration import BaseEvoIntegration

from integrations.classroom.models import GoogleClassroomCourseTwin

import logging

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    def schedule_integration_method_execution(self, method: Callable, **kwargs):
        # TODO schedule a celery task
        method(**kwargs)

    def dispatch(self, action_name: str, course: Course, **kwargs):
        integrations = self.get_enabled_integrations_for(course)

        for integration_cls in integrations:
            integration = integration_cls()
            if action_name in integration.get_available_actions():
                method = getattr(
                    integration, integration_cls.ACTION_HANDLER_PREFIX + action_name
                )
                self.schedule_integration_method_execution(method, **kwargs)
            else:
                logger.warning(
                    f"{str(integration_cls)} doesn't support action {action_name}"
                )

    def get_enabled_integrations_for(
        self,
        course: Course,
    ) -> Iterable[Type[BaseEvoIntegration]]:
        """
        Returns a list of subclasses of `BaseEvoIntegration` representing integrations
        enabled for the given course.

        """
        ret = []

        # NOTE currently, the only integration available is the Google Classroom one, so
        # this is hard coded. in the future, we may dynamically load available integrations
        if GoogleClassroomCourseTwin.objects.filter(course=course).exists():
            ret.append(GoogleClassroomIntegration)

        return ret
