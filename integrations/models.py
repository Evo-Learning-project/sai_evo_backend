from django.db import models
from encrypted_model_fields.fields import EncryptedTextField
from core.validators import validate_str_list

from users.models import User

# TODO create model for google oauth token


class GoogleOAuth2Credentials(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = EncryptedTextField()
    refresh_token = EncryptedTextField()
    id_token = EncryptedTextField()
    scope = models.JSONField(validators=[validate_str_list])

    class Meta:
        verbose_name_plural = "GoogleOAuth2Credentials"
        verbose_name = "GoogleOAuth2Credentials"

    def __str__(self):
        return str(self.user)


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

    _remote_object = None

    # list of fields from the remote twin resource that we're interested
    # in keeping track of, which will be saved into the `data` field when
    # the model instance is created
    REMOTE_OBJECT_FIELDS = []

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk is None:
            # populate `data` with data from the remote object
            # that we're interested in keeping
            remote_object = self.get_remote_object()
            for field in self.REMOTE_OBJECT_FIELDS:
                self.data[field] = remote_object.get(field)
        return super().save(*args, **kwargs)

    def set_remote_object(self, obj):
        self._remote_object = obj

    def get_remote_object(self):
        return self._remote_object
