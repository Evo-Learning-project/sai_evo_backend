from rest_framework import serializers


class RecursiveField(serializers.Serializer):
    """
    Used for serializers that contain self-referencing fields
    """

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class NestedSerializerForeignKeyWritableField(serializers.PrimaryKeyRelatedField):
    """
    Allows related objects to be written using only their pk, but displays them
    using their serializer in read operations
    """

    def __init__(self, **kwargs):
        self.serializer = kwargs.pop("serializer", None)
        if self.serializer is not None and not issubclass(
            self.serializer, serializers.Serializer
        ):
            raise TypeError('"serializer" is not a valid serializer class')

        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False if self.serializer else True

    def to_representation(self, instance):
        # FIXME \|/
        # if self.serializer:
        #     return self.serializer(instance, context=self.context).data
        return super().to_representation(instance)
