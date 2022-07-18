from core.models import HashIdModel
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone


from users.models import User


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

    def save(self, force_no_swap=False, *args, **kwargs):
        # return super().save(*args, **kwargs)
        if self.pk is None:  # creating new instance
            # automatically populate the ordering field based on the ordering of siblings
            setattr(self, "_ordering", self.get_ordering_position())

        if (
            self.pk is not None
            and hasattr(self, "_old__ordering")
            and self._old__ordering != self._ordering
            and not force_no_swap
        ):
            target_ordering, self._ordering = self._ordering, self._old__ordering

            while target_ordering != self._ordering:
                # ! TODO fix endless loop when an item is deleted and there's a "hole" (to reproduce, delete a template rule then try to drag&drop)
                print("TARGET", target_ordering, "SELF", self._ordering)
                to_be_swapped = (
                    self.get_next()
                    if target_ordering > self._ordering
                    else self.get_previous()
                )
                # print("TO BE SWAPPED", to_be_swapped)
                # self.refresh_from_db()
                # type(self).objects.get(
                #     _ordering=self._ordering,
                #     **{
                #         self.ORDER_WITH_RESPECT_TO_FIELD: getattr(
                #             self, self.ORDER_WITH_RESPECT_TO_FIELD
                #         )
                #     },
                # )
                if to_be_swapped is not None:
                    self.swap_ordering_with(to_be_swapped)

        else:
            super().save(*args, **kwargs)

    def get_siblings(self):
        if getattr(self, self.ORDER_WITH_RESPECT_TO_FIELD) is None:
            return []

        return type(self).objects.filter(
            **{
                self.ORDER_WITH_RESPECT_TO_FIELD: getattr(
                    self, self.ORDER_WITH_RESPECT_TO_FIELD
                )
            },
        )

    def get_adjacent(self, step):
        delta = step
        siblings = self.get_siblings()
        for _ in range(0, len(siblings)):
            try:
                return siblings.get(_ordering=self._ordering + delta)
            except type(self).DoesNotExist:
                delta += step

        return None

    def get_next(self):
        return self.get_adjacent(1)

    def get_previous(self):
        return self.get_adjacent(-1)

    def swap_ordering_with(self, other):
        if not isinstance(other, type(self)) or getattr(
            self, self.ORDER_WITH_RESPECT_TO_FIELD
        ) != getattr(other, self.ORDER_WITH_RESPECT_TO_FIELD):
            raise ValidationError("Cannot swap with " + str(other))

        with transaction.atomic():
            self._ordering, other._ordering = other._ordering, self._ordering
            other.save(force_no_swap=True)
            self.save(force_no_swap=True)

    def get_ordering_position(self):
        # get all model instances that reference the same parent
        siblings = self.get_siblings()
        if isinstance(siblings, list) and len(siblings) == 0:
            return 0

        max_ordering = siblings.aggregate(max_ordering=Max("_ordering"))["max_ordering"]
        return max_ordering + 1 if max_ordering is not None else 0


class TimestampableModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def get_default_sibling_cache():
    return {}


class SlotNumberedModel(models.Model):
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

    def get_sibling_slot(self, sibling_entity, participation_pk=None, slot_model=None):
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
    class Meta:
        abstract = True

    @property
    def exercise(self):
        return self.get_sibling_slot("event_instance").exercise


class LockableModel(models.Model):
    """
    A model that is subject to concurrent editing requests in the application, and therefore
    needs to be accessed in mutual exclusion when writing to it. This class only contains
    bookkeeping variables regarding the ownership of the lock - it's up to the RESt API and WS
    to enforce the constraints
    """

    locked_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locked_%(class)ss",
    )
    last_lock_update = models.DateTimeField(null=True, blank=True)
    awaiting_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="awaiting_on_%(class)ss",
    )

    class Meta:
        abstract = True

    def lock(self, user):
        if self.locked_by is None:
            now = timezone.localtime(timezone.now())
            self.locked_by = user
            self.last_lock_update = now
            self.save(update_fields=["locked_by", "last_lock_update"])
            return True

        if self.locked_by != user:
            self.awaiting_users.add(user)

        return self.locked_by == user

    def unlock(self, user):
        if self.locked_by == user:
            now = timezone.localtime(timezone.now())
            if self.awaiting_users.exists():
                first_in_line = self.awaiting_users.first()
                self.locked_by = first_in_line
                self.awaiting_users.remove(first_in_line)
            else:
                self.locked_by = None

            self.last_lock_update = now
            self.save(update_fields=["locked_by", "last_lock_update"])
            return True

        self.awaiting_users.remove(user)

        return self.locked_by is None
