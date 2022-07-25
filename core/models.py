from django.db import models
from hashid_field import HashidAutoField


class HashIdModel(models.Model):
    id = HashidAutoField(primary_key=True)

    class Meta:
        abstract = True
