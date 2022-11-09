from datetime import timedelta
from core.models import HashIdModel
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone


from users.models import User

import logging

logger = logging.getLogger(__name__)


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
        if (
            self.pk is not None
            and hasattr(self, "_old__ordering")
            and self._old__ordering != self._ordering
            and not force_no_swap
        ):
            """
            TODO consider alternative algorithm: when you move an element to the left (right)
            query for all the elements between the element and the target position and move
            them to the right (left) or one position, using qs.update(_ordering=F('_ordering')+1)
            then insert the element into the correct position. This should all be done with a lock

            TODO Alternatively, consider not using save to implicitly swap but rather to use
            a move_by method that tells how many steps (positive or negative) to move by
            """

            # object's ordering has changed: re-arrange ordering of siblings
            # until target ordering is reached for this object
            target_ordering, self._ordering = self._ordering, self._old__ordering

            while target_ordering != self._ordering:
                to_be_swapped = (
                    self.get_next()
                    if target_ordering > self._ordering
                    else self.get_previous()
                )
                if to_be_swapped is not None:
                    if (
                        to_be_swapped._ordering < target_ordering < self._ordering
                        or to_be_swapped._ordering > target_ordering > self._ordering
                    ):
                        # object in the target position doesn't exist, and performing
                        # a swap would take this object past that position; directly
                        # assign the target position to prevent looping
                        self._ordering = target_ordering
                        self.save(force_no_swap=True)
                    else:
                        self.swap_ordering_with(to_be_swapped)
                else:
                    if (
                        target_ordering == 0
                        or target_ordering == self.get_siblings().count() - 1
                    ):
                        # edge case: trying to move the object either to position 0
                        # or to the last position, but the element to be swapped with
                        # has been deleted
                        self._ordering = target_ordering
                        self.save(force_no_swap=True)
        else:
            if self.pk is None:
                # automatically populate the _ordering field based on
                # the ordering of siblings when creating new instance
                self._ordering = self.get_ordering_position()
            # TODO calculate _ordering here and use a lock to avoid race conditions
            super().save(*args, **kwargs)

    def get_siblings(self):
        if getattr(self, self.ORDER_WITH_RESPECT_TO_FIELD) is None:
            return type(self).objects.none()

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
        for _ in range(0, siblings.count()):
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

    # !! this causes race condition
    def get_ordering_position(self):
        # get all model instances that reference the same parent
        siblings = self.get_siblings()
        if siblings.count() == 0:
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


# class SlotNumberedModel(models.Model):
#     parent = models.ForeignKey(
#         "self",
#         null=True,
#         blank=True,
#         related_name="sub_slots",
#         on_delete=models.CASCADE,
#     )
#     slot_number = models.PositiveIntegerField()

#     class Meta:
#         abstract = True

#     @property
#     def event(self):
#         # shortcut to access the slot's event
#         return getattr(self, self.get_container_attribute()).event

#     @property
#     def participation(self):
#         # shortcut to access the slot's participation
#         return getattr(self, self.get_container_attribute()).participation

#     def get_ancestors(self):
#         # returns the slot numbers of all the ancestors of
#         # `self` up to the ancestor base slot
#         ret = [self.slot_number]
#         curr = self
#         while curr.parent is not None:
#             curr = curr.parent
#             ret.append(curr.slot_number)

#         return ret

#     def get_container_attribute(self):
#         # returns the name of the foreign key field to the model that contains the
#         # slots (i.e the many-to-one relation with related_name parameter "slots")
#         for field in type(self)._meta.get_fields():
#             if field.remote_field is not None and field.remote_field.name == "slots":
#                 return field.name

#     def get_sibling_slot(self, sibling_entity, participation_pk=None, slot_model=None):
#         container = getattr(self, self.get_container_attribute())
#         participation = (
#             container.participation
#             if participation_pk is None
#             else container.participations.get(pk=participation_pk)
#         )

#         # walk up to this slot's base slot and record all the ancestors' slot numbers
#         path = reversed(self.get_ancestors())

#         related_slot = None
#         for step in path:
#             # descend the path of ancestors on the related EventInstance,
#             # object, starting from the corresponding base slot down to
#             # the same level of depth as this slot
#             related_slot = getattr(participation, sibling_entity).slots.get(
#                 parent=related_slot, slot_number=step
#             )
#         return related_slot


# class SideSlotNumberedModel(SlotNumberedModel):
#     class Meta:
#         abstract = True

#     @property
#     def exercise(self):
#         return self.get_sibling_slot("event_instance").exercise


class LockableModel(models.Model):
    """
    A model that is subject to concurrent editing requests in the application, and therefore
    needs to be accessed in mutual exclusion when writing to it. This class only contains
    bookkeeping variables regarding the ownership of the lock - it's up to the RESt API and WS
    to enforce the constraints
    """

    # TODO actually enforce the locking at api level

    # user who currently has ownership of the lock
    _locked_by = models.ForeignKey(
        User,
        db_column="locked_by",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locked_%(class)ss",
    )

    # last time the owner of the lock was updated
    last_lock_update = models.DateTimeField(null=True, blank=True)

    # last time the owner of the lock sent a heartbeat
    last_heartbeat = models.DateTimeField(null=True, blank=True)

    # contains users that are in queue for acquiring the lock on the instance
    awaiting_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="awaiting_on_%(class)ss",
    )

    LOCK_TIMEOUT_SECONDS = 40

    class Meta:
        abstract = True

    @property
    def locked_by(self):
        """
        Before returning the user who has the lock over the instance, check if
        the lock is expired, i.e. the last heartbeat is older than LOCK_TIMEOUT_SECONDS.
        If so, pass the lock onto the first user in line or release the lock if the
        waiting list is empty.
        """
        if self.has_lock_timed_out():
            update_fields = ["_locked_by"]
            if self.awaiting_users.exists():
                # pass lock onto first user in line
                first_in_line = self.awaiting_users.first()
                self._locked_by = first_in_line
                self.awaiting_users.remove(first_in_line)

                # automatically send a heartbeat to prevent the lock from
                # staying in a timed out state, which would cause it to be
                # released immediately if accessed until the first heartbeat
                # is sent by the new user who holds it
                now = timezone.localtime(timezone.now())
                self.last_heartbeat = now
                update_fields.append("last_heartbeat")

            else:
                self._locked_by = None

            self.save(update_fields=update_fields)

        return self._locked_by

    @locked_by.setter
    def locked_by(self, value):
        self._locked_by = value

    def try_lock(self, user):
        # TODO manage race conditions for all methods
        """
        Locks instance is not locked by another user, otherwise adds the requesting
        user to the waiting list for this instance.

        Returns whether the user successfully acquired the lock.
        """
        now = timezone.localtime(timezone.now())

        if self.locked_by == user:
            # if the instance is already locked by the requesting user,
            # treat this as a heartbeat
            return self.heartbeat(user)

        if self.locked_by is None:
            self.locked_by = user

            self.last_lock_update = now
            self.last_heartbeat = now

            self.save(
                update_fields=["_locked_by", "last_lock_update", "last_heartbeat"]
            )
            return True

        # another user owns the lock; add current user to waiting list
        if self.locked_by != user:
            self.awaiting_users.add(user)

        return self.locked_by == user

    def unlock_or_give_up(self, user):
        """
        Releases lock over the instance if user owns it, or removes them
        from the waiting list.

        If the requesting user is the owner of the lock, the lock is then
        given to the first user in the waiting list.

        Returns True if no one detains the lock on the object anymore,
        False otherwise.
        """
        # TODO race condition - what happens if a user leaves the waiting line at the same time it is given the lock?
        if self.locked_by == user:
            if self.awaiting_users.exists():
                first_in_line = self.awaiting_users.first()
                self.locked_by = first_in_line
                self.awaiting_users.remove(first_in_line)
            else:
                self.locked_by = None

            now = timezone.localtime(timezone.now())
            self.last_lock_update = now
            self.last_heartbeat = now

            self.save(
                update_fields=["_locked_by", "last_lock_update", "last_heartbeat"]
            )
            return True

        self.awaiting_users.remove(user)

        return self.locked_by is None

    def heartbeat(self, user):
        """
        Updates the value of last_heartbeat to now if the requesting
        user owns the lock on the instance.
        """
        if self.locked_by == user:
            now = timezone.localtime(timezone.now())
            self.last_heartbeat = now
            self.save(update_fields=["last_heartbeat"])
            return True
        return False

    def has_lock_timed_out(self):
        """
        Returns True if the last heartbeat sent to this instance
        is older than `LOCK_TIMEOUT_SECONDS`
        """
        if self.last_heartbeat is None:
            # logger.warning(str(self) + " last heartbeat is None")
            return True

        now = timezone.localtime(timezone.now())

        return self.last_heartbeat < now - timedelta(seconds=self.LOCK_TIMEOUT_SECONDS)
