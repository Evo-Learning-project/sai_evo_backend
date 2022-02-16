from core.models import UUIDModel
from django.core.exceptions import ValidationError
from django.db import models, transaction


class TrackFieldsMixin(models.Model):
    """
    Abstract model used to track changes to a model's fields before
    writing those changes to the db
    """

    TRACKED_FIELDS = []  # list of field names

    class Meta:
        abstract = True

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        for fieldname in cls.TRACKED_FIELDS:
            setattr(instance, f"_old_{fieldname}", getattr(instance, fieldname))

        return instance


class OrderableModel(TrackFieldsMixin):
    ORDER_WITH_RESPECT_TO_FIELD = ""  # field name
    TRACKED_FIELDS = ["_ordering"]

    _ordering = models.PositiveIntegerField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk is None:  # creating new instance
            # automatically populate the ordering field based on the ordering of siblings
            setattr(self, "_ordering", self.get_ordering_position())

        if self._old__ordering != self._ordering:
            # get model instance that currently has _ordering value
            # that's being assigned to this instance
            to_be_swapped = type(self).objects.get(
                _ordering=self._ordering,
                **{
                    self.ORDER_WITH_RESPECT_TO_FIELD: getattr(
                        self, self.ORDER_WITH_RESPECT_TO_FIELD
                    )
                },
            )
            self.swap_ordering_with(to_be_swapped)

        else:
            super().save(*args, **kwargs)

    def swap_ordering_with(self, other):
        if not isinstance(other, type(self)) or getattr(
            self, self.ORDER_WITH_RESPECT_TO_FIELD
        ) != getattr(other, self.ORDER_WITH_RESPECT_TO_FIELD):
            raise ValidationError("Cannot swap with " + str(other))

        with transaction.atomic():
            self._ordering, other._ordering = other._ordering, self._ordering
            other.save()
            self.save()

    def get_ordering_position(self):
        # filter to get parent
        filter_kwarg = {
            self.ORDER_WITH_RESPECT_TO_FIELD: getattr(
                self, self.ORDER_WITH_RESPECT_TO_FIELD
            )
        }

        # get all model instances that reference the same parent
        siblings = type(self).objects.filter(**filter_kwarg)

        max_ordering = siblings.aggregate(max_ordering=Max("_ordering"))["max_ordering"]
        return max_ordering + 1 if max_ordering is not None else 0


class TimestampableModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SlotNumberedModel(UUIDModel):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="sub_slots",
        on_delete=models.CASCADE,
    )
    slot_number = models.PositiveIntegerField()

    class Meta:
        abstract = True

    @property
    def event(self):
        # shortcut to access the slot's event
        return getattr(self, self.get_container_attribute()).event

    @property
    def participation(self):
        # shortcut to access the slot's participation
        return getattr(self, self.get_container_attribute()).participation

    def get_ancestors(self):
        # returns the slot numbers of all the ancestors of
        # `self` up to the ancestor base slot
        ret = [self.slot_number]
        curr = self
        while curr.parent is not None:
            curr = curr.parent
            ret.append(curr.slot_number)

        return ret

    def get_container_attribute(self):
        # returns the name of the foreign key field to the model that contains the
        # slots (i.e the many-to-one relation with related_name parameter "slots")
        for field in type(self)._meta.get_fields():
            if field.remote_field is not None and field.remote_field.name == "slots":
                return field.name

    def get_sibling_slot(self, sibling_entity, participation_pk=None):
        container = getattr(self, self.get_container_attribute())
        participation = (
            container.participation
            if participation_pk is None
            else container.participations.get(pk=participation_pk)
        )

        # walk up to this slot's base slot and record all the ancestors' slot numbers
        path = reversed(self.get_ancestors())

        related_slot = None
        for step in path:
            # descend the path of ancestors on the related EventInstance,
            # object, starting from the corresponding base slot down to
            # the same level of depth as this slot
            related_slot = getattr(participation, sibling_entity).slots.get(
                parent=related_slot, slot_number=step
            )
        return related_slot


class SideSlotNumberedModel(SlotNumberedModel):
    # TODO find a better name for the class
    class Meta:
        abstract = True

    @property
    def exercise(self):
        return self.get_sibling_slot("event_instance").exercise
