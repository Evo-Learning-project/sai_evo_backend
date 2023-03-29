from core.celery import app

from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from celery.exceptions import MaxRetriesExceededError

from django.utils import timezone

import logging

logger = logging.getLogger(__name__)


@app.task(bind=True, retry_backoff=True, max_retries=5)
def publish_scheduled_node(self, model_name, pk):
    """
    Publishes a node that is drafted and has passed its schedule datetime
    """
    from course_tree.models import SchedulableModel

    try:
        # Get the ContentType for the given model app label and model name
        model_class = apps.get_model("course_tree", model_name)
        content_type = ContentType.objects.get_for_model(model_class)
        node = content_type.get_object_for_this_type(id=pk)
        if not isinstance(node, SchedulableModel):
            logger.critical(
                f"A publish_scheduled_node task was scheduled for\
                non-schedulable node {str(node)}"
            )
            return
        if not node.is_draft:
            logger.info(
                f"Skipping publish for {str(node)} because it is\
                not in state draft"
            )
            return

        now = timezone.localtime(timezone.now())
        if node.schedule_publish_at is None or node.schedule_publish_at > now:
            logger.info(
                f"Skipping publish for {str(node)} because its schedule_publish_at\
                is {node.schedule_publish_at}"
            )
            return

        node.publish()
    except (LookupError, ContentType.DoesNotExist):
        logger.critical(f"Couldn't find content type {model_name}")
        return
