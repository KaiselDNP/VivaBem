from .models import Notification


def notify(*, recipient, kind, title, message, target_url=""):
    return Notification.objects.create(
        recipient=recipient,
        kind=kind,
        title=title,
        message=message,
        target_url=target_url,
    )
