from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.needs.models import HelpRequest, InterestStatus, Need, NeedCategory, ProfessionalInterest
from apps.notifications.models import Notification, NotificationKind
from apps.relationships.models import FamilyLink, FamilyLinkStatus, FamilyPermission

from ..models import ChatBlock, ChatMessage, ChatModerationEvent, Conversation
from ..moderation import moderate_message
from ..services import get_or_create_conversation


class ChatAccessTests(TestCase):
    password = "UmaSenhaBemSegura123!"

    def setUp(self):
        user_model = get_user_model()
        self.senior = user_model.objects.create_user(
            email="idosa@example.com",
            password=self.password,
            first_name="Maria",
            role=UserRole.SENIOR,
        )
        self.family = user_model.objects.create_user(
            email="familiar@example.com",
            password=self.password,
            first_name="Carlos",
            role=UserRole.FAMILY,
        )
        self.professional = user_model.objects.create_user(
            email="profissional@example.com",
            password=self.password,
            first_name="Pablo",
            role=UserRole.PROFESSIONAL,
        )
        self.outsider = user_model.objects.create_user(
            email="outro@example.com", password=self.password, role=UserRole.PROFESSIONAL
        )
        self.admin = user_model.objects.create_superuser(
            email="admin@example.com", password=self.password
        )
        self.link = FamilyLink.objects.create(
            senior=self.senior,
            family=self.family,
            requested_by=self.family,
            status=FamilyLinkStatus.APPROVED,
        )
        self.permissions = FamilyPermission.objects.create(
            link=self.link, can_view_professional_interests=True
        )
        need = Need.objects.create(
            senior=self.senior,
            title="Ajuda com tecnologia",
            category=NeedCategory.DIGITAL,
            description="Configurar um aplicativo.",
        )
        help_request = HelpRequest.objects.create(
            need=need, details="Preciso de orientação para usar o aplicativo."
        )
        ProfessionalInterest.objects.create(
            help_request=help_request,
            professional=self.professional,
            message="Posso ajudar.",
            status=InterestStatus.ACCEPTED,
        )

    def start_chat(self, actor, target):
        self.client.force_login(actor)
        return self.client.post(reverse("chat:start", args=(target.pk,)))

    def test_only_authorized_relationships_start_chat(self):
        self.assertEqual(self.start_chat(self.senior, self.family).status_code, 302)
        Conversation.objects.all().delete()
        self.assertEqual(self.start_chat(self.professional, self.senior).status_code, 302)
        Conversation.objects.all().delete()
        self.assertEqual(self.start_chat(self.family, self.professional).status_code, 302)
        Conversation.objects.all().delete()
        self.assertEqual(self.start_chat(self.outsider, self.senior).status_code, 403)

    def test_family_permission_controls_professional_chat(self):
        self.permissions.can_view_professional_interests = False
        self.permissions.save(update_fields=("can_view_professional_interests",))
        self.assertEqual(self.start_chat(self.family, self.professional).status_code, 403)

    def test_message_is_sent_and_marked_read(self):
        conversation, _ = get_or_create_conversation(self.senior, self.professional)
        self.client.force_login(self.senior)
        self.client.post(
            reverse("chat:detail", args=(conversation.pk,)),
            {"body": "Podemos combinar os detalhes do atendimento?"},
        )
        chat_message = ChatMessage.objects.get()
        self.assertIsNone(chat_message.read_at)
        self.client.force_login(self.professional)
        self.client.get(reverse("chat:detail", args=(conversation.pk,)))
        chat_message.refresh_from_db()
        self.assertIsNotNone(chat_message.read_at)

    def test_moderation_removes_message_and_notifies_admin_without_body(self):
        conversation, _ = get_or_create_conversation(self.senior, self.professional)
        blocked_body = "vou te machucar"
        self.client.force_login(self.senior)
        response = self.client.post(
            reverse("chat:detail", args=(conversation.pk,)), {"body": blocked_body}, follow=True
        )
        self.assertContains(response, "Mensagem removida por possível uso indevido")
        self.assertFalse(ChatMessage.objects.exists())
        self.assertTrue(ChatModerationEvent.objects.filter(sender=self.senior).exists())
        notification = Notification.objects.get(
            recipient=self.admin, kind=NotificationKind.CHAT_MODERATION
        )
        self.assertNotIn(blocked_body, notification.message)

    def test_normalization_and_user_block(self):
        self.assertTrue(moderate_message("Seu INÚTIL!!!").blocked)
        conversation, _ = get_or_create_conversation(self.senior, self.professional)
        self.client.force_login(self.senior)
        self.client.post(reverse("chat:block", args=(conversation.pk,)))
        self.assertTrue(ChatBlock.objects.filter(blocker=self.senior).exists())
        self.client.force_login(self.professional)
        self.client.post(
            reverse("chat:detail", args=(conversation.pk,)),
            {"body": "Mensagem que não será salva."},
        )
        self.assertFalse(ChatMessage.objects.exists())

    def test_rate_limit_stops_excessive_messages(self):
        conversation, _ = get_or_create_conversation(self.senior, self.professional)
        for index in range(10):
            ChatMessage.objects.create(
                conversation=conversation, sender=self.senior, body=f"Mensagem segura {index}"
            )
        self.client.force_login(self.senior)
        response = self.client.post(
            reverse("chat:detail", args=(conversation.pk,)),
            {"body": "Mensagem acima do limite."},
            follow=True,
        )
        self.assertContains(response, "Muitas mensagens foram enviadas")
        self.assertEqual(ChatMessage.objects.count(), 10)
