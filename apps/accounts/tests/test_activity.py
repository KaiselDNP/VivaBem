from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserRole


class UserActivityMiddlewareTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="atividade@example.com",
            password="FraseSegura123!",
            role=UserRole.SENIOR,
        )

    def test_authenticated_request_records_approximate_activity(self):
        self.client.force_login(self.user)
        before = timezone.now()

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_activity_at)
        self.assertGreaterEqual(self.user.last_activity_at, before)
        self.assertTrue(self.user.is_online)

    def test_recent_session_is_not_written_on_every_request(self):
        self.client.force_login(self.user)
        self.client.get(reverse("accounts:dashboard"))
        self.user.refresh_from_db()
        first_activity = self.user.last_activity_at
        self.user.last_activity_at = first_activity - timedelta(days=1)
        self.user.save(update_fields=("last_activity_at",))

        self.client.get(reverse("accounts:dashboard"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.last_activity_at, first_activity - timedelta(days=1))
