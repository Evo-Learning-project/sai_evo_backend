from typing import Callable, Iterable, Type

import logging

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    def schedule_integration_method_execution(self, method: Callable, **kwargs):
        # TODO schedule a celery task
        try:
            method(**kwargs)
        except:
            pass

    def dispatch(self, action_name: str, course: "Course", **kwargs):
        integrations = self.get_enabled_integrations_for(course)

        # loop over all the integrations enabled for the given course, and
        # for each of them, if the dispatched action is supported, schedule
        # the corresponding handler to be run with the given arguments
        for integration_cls in integrations:
            integration = integration_cls()
            # check the current integration supports the dispatched action
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
        if GoogleClassroomCourseTwin.objects.filter(course=course).exists():
            ret.append(GoogleClassroomIntegration)

        return ret
