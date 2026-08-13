from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.needs.models import Need, NeedCategory
from apps.notifications.models import Notification

from ..models import FamilyLink, FamilyLinkStatus


class FamilyLinkPermissionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.senior = user_model.objects.create_user(
            email="idosa@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Helena",
            role=UserRole.SENIOR,
        )
        self.family = user_model.objects.create_user(
            email="familiar@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Carlos",
            role=UserRole.FAMILY,
        )
        self.need = Need.objects.create(
            senior=self.senior,
            title="Necessidade reservada",
            category=NeedCategory.DAILY_TASKS,
            description="Informação visível somente após autorização específica.",
        )

    def request_and_approve_link(self):
        self.client.force_login(self.family)
        self.client.post(
            reverse("relationships:request"),
            {"senior_email": self.senior.email},
        )
        link = FamilyLink.objects.get(senior=self.senior, family=self.family)
        self.client.force_login(self.senior)
        self.client.post(reverse("relationships:respond", args=(link.pk, "approve")))
        link.refresh_from_db()
        return link

    def test_link_requires_senior_approval_and_starts_without_permissions(self):
        self.client.force_login(self.family)
        response = self.client.post(
            reverse("relationships:request"),
            {"senior_email": self.senior.email},
        )
        self.assertRedirects(response, reverse("relationships:list"))
        link = FamilyLink.objects.get(senior=self.senior, family=self.family)
        self.assertEqual(link.status, FamilyLinkStatus.PENDING)
        self.assertTrue(Notification.objects.filter(recipient=self.senior).exists())

        self.client.force_login(self.senior)
        self.client.post(reverse("relationships:respond", args=(link.pk, "approve")))
        link.refresh_from_db()
        self.assertEqual(link.status, FamilyLinkStatus.APPROVED)
        self.assertFalse(link.permissions.can_view_needs)
        self.assertFalse(link.permissions.can_view_requests)

    def test_family_only_sees_information_after_specific_permission(self):
        link = self.request_and_approve_link()
        overview_url = reverse("relationships:senior_overview", args=(link.pk,))

        self.client.force_login(self.family)
        hidden_response = self.client.get(overview_url)
        self.assertNotContains(hidden_response, self.need.title)

        self.client.force_login(self.senior)
        self.client.post(
            reverse("relationships:permissions", args=(link.pk,)),
            {
                "can_view_needs": "on",
                "can_view_requests": "",
                "can_view_professional_interests": "",
                "can_receive_notifications": "",
            },
        )
        self.client.force_login(self.family)
        allowed_response = self.client.get(overview_url)
        self.assertContains(allowed_response, self.need.title)

    def test_family_cannot_change_own_permissions(self):
        link = self.request_and_approve_link()
        self.client.force_login(self.family)
        response = self.client.post(
            reverse("relationships:permissions", args=(link.pk,)),
            {
                "can_view_needs": "on",
                "can_view_requests": "on",
                "can_view_professional_interests": "on",
                "can_receive_notifications": "on",
            },
        )
        self.assertEqual(response.status_code, 403)
        link.permissions.refresh_from_db()
        self.assertFalse(link.permissions.can_view_needs)
