def send_in_app(notification) -> bool:
    """
    30.3: the in-app channel is definitionally always "delivered" the
    moment the Notification row + a real-time push exist — there's no
    separate network hop that can fail the way email/SMS can. Kept as
    its own function (rather than skipping delivery tracking for this
    channel entirely) so app/notifications/delivery.py can log a
    uniform NotificationDelivery row for every channel, not special-
    case this one.
    """
    return True
