from django.urls import reverse

from apps.notifications.models import NotificationKind
from apps.notifications.services import notify
from apps.relationships.services import authorized_family_users


def notify_family_about_request(help_request, title, message, *, interests=False):
    permissions = ["can_receive_notifications"]
    permissions.append("can_view_professional_interests" if interests else "can_view_requests")
    for family in authorized_family_users(help_request.senior, *permissions):
        notify(
            recipient=family,
            kind=(
                NotificationKind.PROFESSIONAL_INTEREST
                if interests
                else NotificationKind.HELP_REQUEST
            ),
            title=title,
            message=message,
            target_url=reverse("relationships:list"),
        )
