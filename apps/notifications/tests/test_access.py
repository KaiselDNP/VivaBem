from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole

from ..models import Notification, NotificationKind


class NotificationAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            email="dono@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.SENIOR,
        )
        self.other = user_model.objects.create_user(
            email="outro@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.FAMILY,
        )
        self.notification = Notification.objects.create(
            recipient=self.owner,
            kind=NotificationKind.HELP_REQUEST,
            title="Atualização",
            message="Sua solicitação recebeu uma atualização.",
        )

    def test_user_only_lists_own_notifications(self):
        Notification.objects.create(
            recipient=self.other,
            kind=NotificationKind.FAMILY_LINK,
            title="Mensagem privada de outro usuário",
            message="Conteúdo privado.",
        )
        self.client.force_login(self.owner)
        response = self.client.get(reverse("notifications:list"))
        self.assertContains(response, self.notification.title)
        self.assertContains(response, "Novo")
        self.assertContains(response, "Marcar como visto")
        self.assertNotContains(response, "Mensagem privada de outro usuário")

    def test_user_cannot_mark_another_users_notification_as_read(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("notifications:mark_read", args=(self.notification.pk,))
        )
        self.assertEqual(response.status_code, 404)
        self.notification.refresh_from_db()
        self.assertIsNone(self.notification.read_at)
