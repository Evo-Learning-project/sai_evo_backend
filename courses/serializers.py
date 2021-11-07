from rest_framework import serializers


class HiddenFieldsModelSerializer(serializers.ModelSerializer):
    """
    Used to conditionally show certain fields only when the `context` argument
    is provided and contains key `show_hidden_fields` with a truthy value
    """

    def __init__(self, *args, **kwargs):
        context = kwargs.get("context", None)
        if context is not None and context.get("show_hidden_fields", False):
            self.Meta.fields.extend(self.Meta.hidden_fields)
        super().__init__(*args, **kwargs)
