import json
from django.core.exceptions import ValidationError


def validate_list(value):
    if not isinstance(value, list):
        raise ValidationError("Value must be a list")


def validate_str_list(value):
    if not isinstance(value, list):
        raise ValidationError("Value must be a list")
    if any(not isinstance(e, str) for e in value):
        raise ValidationError("Value must be a list or strings")
