from django.db import models


class RemoteTwinResource(models.Model):
    """
    An abstract model representing a "twin" resource which is associated
    to a model instance on Evo. This is used to pair certain models, such
    as Courses, to objects on integrated services, such as Google Classroom
    courses.

    The models that subclass RemoteTwinResource will have a foreign key
    to a specific model which is being paired with a remote resource.
    """

    # id of the remote resource associated to the model referenced
    # by the specific foreign key possessed by subclasses of this model
    remote_object_id = models.TextField(blank=False)

    # extra data about the remote object which may be used by the application.
    # usage of this field depends on the concrete sub-model and type of resource
    data = models.JSONField(default=dict)

    class Meta:
        abstract = True
