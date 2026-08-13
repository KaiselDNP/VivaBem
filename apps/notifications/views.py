from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()[:100]
    return render(
        request,
        "notifications/list.html",
        {"notifications": notifications},
    )


@login_required
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notification.read_at:
        notification.read_at = timezone.now()
        notification.save(update_fields=("read_at",))
    if notification.target_url.startswith("/") and not notification.target_url.startswith("//"):
        return redirect(notification.target_url)
    return redirect("notifications:list")


@login_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    return redirect("notifications:list")
