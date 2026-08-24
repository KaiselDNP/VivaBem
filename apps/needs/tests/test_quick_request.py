from typing import ClassVar

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.notifications.models import Notification, NotificationKind
from apps.relationships.models import FamilyLink, FamilyLinkStatus, FamilyPermission

from ..models import HelpRequest


class QuickHelpRequestTests(TestCase):
    password = "FraseSegura123!"
    form_data: ClassVar[dict[str, str]] = {
        "title": "Ajuda com celular",
        "category": "digital",
        "details": "Preciso aprender a usar um aplicativo.",
        "region": "Avaré-SP",
        "priority": "routine",
        "preferred_service_mode": "both",
    }

    def setUp(self):
        users = get_user_model()
        self.senior = users.objects.create_user(
            email="senior@example.com", password=self.password, role=UserRole.SENIOR
        )
        self.family = users.objects.create_user(
            email="family@example.com", password=self.password, role=UserRole.FAMILY
        )
        self.link = FamilyLink.objects.create(
            senior=self.senior,
            family=self.family,
            requested_by=self.family,
            status=FamilyLinkStatus.APPROVED,
        )
        self.permissions = FamilyPermission.objects.create(link=self.link)

    def test_senior_creates_complete_request_in_one_flow(self):
        self.client.force_login(self.senior)
        response = self.client.post(reverse("needs:quick_request"), self.form_data)
        request = HelpRequest.objects.select_related("need").get()
        self.assertRedirects(response, reverse("needs:request_detail", args=(request.pk,)))
        self.assertEqual(request.need.senior, self.senior)
        self.assertEqual(request.created_by, self.senior)

    def test_family_needs_explicit_permission(self):
        self.client.force_login(self.family)
        url = reverse("needs:assisted_quick_request", args=(self.senior.pk,))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.permissions.can_create_requests = True
        self.permissions.save(update_fields=("can_create_requests",))
        response = self.client.post(url, self.form_data)
        request = HelpRequest.objects.get()
        self.assertRedirects(
            response, reverse("relationships:senior_overview", args=(self.link.pk,))
        )
        self.assertEqual(request.created_by, self.family)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.senior, kind=NotificationKind.HELP_REQUEST
            ).exists()
        )

    def test_unrelated_family_cannot_create_for_senior(self):
        other = get_user_model().objects.create_user(
            email="other@example.com", password=self.password, role=UserRole.FAMILY
        )
        self.client.force_login(other)
        response = self.client.post(
            reverse("needs:assisted_quick_request", args=(self.senior.pk,)), self.form_data
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(HelpRequest.objects.exists())
