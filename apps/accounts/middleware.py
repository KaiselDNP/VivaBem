from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.utils import timezone


class UserActivityMiddleware:
    """Store an approximate last activity time without logging navigation details."""

    session_key = "vivabem_last_activity_write"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_active:
            self._record_activity(request)
        return self.get_response(request)

    def _record_activity(self, request):
        now = timezone.now()
        previous_write = request.session.get(self.session_key, 0)
        update_interval = max(30, settings.USER_ACTIVITY_UPDATE_SECONDS)
        try:
            elapsed = now.timestamp() - float(previous_write)
        except (TypeError, ValueError):
            elapsed = update_interval

        if elapsed < update_interval:
            return
        try:
            get_user_model().objects.filter(pk=request.user.pk).update(last_activity_at=now)
        except DatabaseError:
            return
        request.user.last_activity_at = now
        request.session[self.session_key] = int(now.timestamp())
