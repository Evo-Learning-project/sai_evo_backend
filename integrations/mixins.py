class IntegrationModelMixin:
    """
    A mixin for models that interact with the integration registry.
    This is currently used to pass information to the model to control
    whether it should fire an event to the integration registry.

    A boolean variable with name equal to the value of `FIRE_INTEGRATION_EVENT` may
    be set on the model to indicate whether an optional event should be fired to
    the integration registry. The model may check for this variable to decide whether
    to fire the event.
    """

    FIRE_INTEGRATION_EVENT = "_fire_integration_event"
