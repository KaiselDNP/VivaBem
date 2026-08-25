from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.notifications.models import Notification, NotificationKind
from apps.professionals.models import ProfessionalProfile, VerificationStatus

from ..models import AdminAnnouncement, AdminAuditLog, AnnouncementAudience, AuditAction


class AdministrationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Administrador",
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.professional_user = user_model.objects.create_user(
            email="profissional@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Ana",
            role=UserRole.PROFESSIONAL,
        )
        self.profile = ProfessionalProfile.objects.create(
            user=self.professional_user,
            profession="Terapeuta ocupacional",
            specialty="Tecnologia assistiva",
            service_region="Avaré-SP",
            council="CREFITO",
            registration_number="12345-SP",
        )
        self.family = user_model.objects.create_user(
            email="familiar@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.FAMILY,
        )

    def test_staff_without_admin_role_is_denied(self):
        self.family.is_staff = True
        self.family.save(update_fields=("is_staff",))
        self.client.force_login(self.family)
        response = self.client.get(reverse("moderation:admin_users"))
        self.assertEqual(response.status_code, 403)

    def test_admin_menu_highlights_current_section(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("moderation:admin_users"))

        self.assertContains(response, "Central de gestão")
        self.assertContains(response, 'class="is-active" aria-current="page"', count=1)
        self.assertContains(response, "Contas e acessos")

    def test_user_management_shows_account_summary(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("moderation:admin_users"))

        self.assertEqual(response.context["user_summary"]["total"], 3)
        self.assertEqual(response.context["user_summary"]["active"], 3)
        self.assertEqual(response.context["user_summary"]["professionals"], 1)
        self.assertContains(response, "Contas cadastradas")

    def test_user_management_shows_online_and_last_activity_only_to_admin(self):
        self.professional_user.last_activity_at = timezone.now()
        self.professional_user.save(update_fields=("last_activity_at",))
        self.family.last_activity_at = timezone.now() - timedelta(minutes=10)
        self.family.save(update_fields=("last_activity_at",))
        self.client.force_login(self.admin)

        response = self.client.get(reverse("moderation:admin_users"))

        self.assertContains(response, "Último uso")
        self.assertContains(response, "Online agora", count=2)
        family_local_activity = timezone.localtime(self.family.last_activity_at)
        self.assertContains(response, family_local_activity.strftime("%d/%m/%Y"))

    def test_django_admin_uses_vivabem_interface(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administração técnica")
        self.assertContains(response, "Gestão visual")
        self.assertContains(response, "Voltar ao sistema")

    def test_admin_can_verify_complete_professional(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderation:admin_professional_review", args=(self.profile.pk,)),
            {
                "verification_status": VerificationStatus.VERIFIED,
                "verification_notes": "Dados conferidos administrativamente para o protótipo.",
            },
        )
        self.assertRedirects(response, reverse("moderation:admin_professionals"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.VERIFIED)
        self.assertEqual(self.profile.verified_by, self.admin)
        self.assertIsNotNone(self.profile.verified_at)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.professional_user,
                kind=NotificationKind.PROFESSIONAL_REVIEW,
            ).exists()
        )
        self.assertTrue(
            AdminAuditLog.objects.filter(
                action=AuditAction.PROFESSIONAL_REVIEW,
                target_id=self.profile.pk,
            ).exists()
        )

    def test_incomplete_professional_cannot_be_verified(self):
        self.profile.specialty = ""
        self.profile.save(update_fields=("specialty",))
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderation:admin_professional_review", args=(self.profile.pk,)),
            {
                "verification_status": VerificationStatus.VERIFIED,
                "verification_notes": "Tentativa de aprovação.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.PENDING)

    def test_admin_can_deactivate_regular_user_and_action_is_audited(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "moderation:admin_user_status",
                args=(self.family.pk, "deactivate"),
            )
        )
        self.assertRedirects(response, reverse("moderation:admin_users"))
        self.family.refresh_from_db()
        self.assertFalse(self.family.is_active)
        self.assertTrue(
            AdminAuditLog.objects.filter(
                action=AuditAction.USER_STATUS,
                target_id=self.family.pk,
            ).exists()
        )

    def test_admin_cannot_deactivate_own_account(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "moderation:admin_user_status",
                args=(self.admin.pk, "deactivate"),
            )
        )
        self.assertEqual(response.status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_sends_notice_to_one_selected_user_only(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderation:admin_announcement_create"),
            {
                "audience": AnnouncementAudience.INDIVIDUAL,
                "recipient": self.family.pk,
                "title": "Atualização importante",
                "message": "Confira uma atualização na plataforma VivaBem.",
            },
        )
        self.assertRedirects(response, reverse("moderation:admin_announcements"))
        announcement = AdminAnnouncement.objects.get()
        self.assertEqual(announcement.recipients_count, 1)
        self.assertEqual(announcement.recipient, self.family)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.family,
                kind=NotificationKind.ADMIN_NOTICE,
                title="Atualização importante",
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.professional_user,
                kind=NotificationKind.ADMIN_NOTICE,
            ).exists()
        )
        self.assertTrue(AdminAuditLog.objects.filter(action=AuditAction.NOTICE_SENT).exists())

    def test_admin_can_send_notice_to_active_users_of_one_role(self):
        user_model = get_user_model()
        active_senior = user_model.objects.create_user(
            email="idosa@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.SENIOR,
        )
        inactive_senior = user_model.objects.create_user(
            email="idosa-inativa@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.SENIOR,
            is_active=False,
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderation:admin_announcement_create"),
            {
                "audience": AnnouncementAudience.SENIORS,
                "recipient": "",
                "title": "Aviso para pessoas idosas",
                "message": "Há uma atualização disponível no painel.",
            },
        )
        self.assertRedirects(response, reverse("moderation:admin_announcements"))
        self.assertTrue(
            Notification.objects.filter(
                recipient=active_senior,
                kind=NotificationKind.ADMIN_NOTICE,
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=inactive_senior,
                kind=NotificationKind.ADMIN_NOTICE,
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.family,
                kind=NotificationKind.ADMIN_NOTICE,
            ).exists()
        )

    def test_individual_notice_requires_recipient(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderation:admin_announcement_create"),
            {
                "audience": AnnouncementAudience.INDIVIDUAL,
                "recipient": "",
                "title": "Aviso sem destinatário",
                "message": "Esta mensagem não deve ser enviada.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Escolha a conta que receberá o aviso")
        self.assertFalse(AdminAnnouncement.objects.exists())

    def test_regular_user_cannot_send_admin_notice(self):
        self.client.force_login(self.family)
        response = self.client.post(
            reverse("moderation:admin_announcement_create"),
            {
                "audience": AnnouncementAudience.ALL_USERS,
                "title": "Tentativa indevida",
                "message": "Esta mensagem não deve ser enviada.",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(AdminAnnouncement.objects.exists())
