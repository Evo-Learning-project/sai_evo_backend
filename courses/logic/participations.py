from datetime import timedelta
from time import time
from typing import Optional
from courses.models import Event, EventParticipation
from users.models import User
from django.utils import timezone


def get_effective_time_limit(user: User, event: Event) -> Optional[int]:
    """Returns the effective time limit, in seconds, for the given
    user and event if one exists; otherwise returns None.

    The effective time limit is the time_limit_seconds property of the
    event if no exception is in place for the user, otherwise it's the
    time specified in the exception.

    Args:
        user (User): the user to which the time limit applies
        event (Event): the event that applies the time limit

    Returns:
        Optional[int]: a number of seconds representing the time limit, or None
        if no time limit applies
    """

    if event.time_limit_rule != Event.TIME_LIMIT:
        return None

    # if user has a time limit exception, return that time
    try:
        time_limit_exception = [
            t for [e, t] in event.time_limit_exceptions if e == user.email
        ][0]
        return float(time_limit_exception)
    except IndexError:
        # no exception for user, return standard time limit for event
        return float(event.time_limit_seconds)


TIME_LIMIT_GRACE_SECONDS = 30


def is_time_up(
    participation: EventParticipation, grace_period=TIME_LIMIT_GRACE_SECONDS
) -> bool:
    """Returns True iff time is up for the given participation, i.e.
    the current timestamp is past the begin timestamp of the participation
    plus the time limit allowed plus a grace period.

    Args:
        participation (EventParticipation): the participation for which
        to check whether the time is up

    Returns:
        bool: True if time has run out for the participation, False otherwise
    """
    time_limit = get_effective_time_limit(participation.user, participation.event)

    if time_limit is None:
        return False

    now = timezone.localtime(timezone.now())

    return now > (
        participation.begin_timestamp + timedelta(seconds=time_limit + grace_period)
    )
