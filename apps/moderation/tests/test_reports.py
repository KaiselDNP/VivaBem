from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.notifications.models import Notification, NotificationKind

from ..models import AdminAuditLog, AuditAction, Report, ReportCategory, ReportStatus


class ReportFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.reporter = user_model.objects.create_user(
            email="familiar@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Carlos",
            role=UserRole.FAMILY,
        )
        self.target = user_model.objects.create_user(
            email="profissional@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Ana",
            role=UserRole.PROFESSIONAL,
        )
        self.other = user_model.objects.create_user(
            email="outro@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.SENIOR,
        )
        self.admin = user_model.objects.create_user(
            email="admin@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Administrador",
            role=UserRole.ADMIN,
            is_staff=True,
        )

    def create_report(self):
        return Report.objects.create(
            reporter=self.reporter,
            reported_user=self.target,
            category=ReportCategory.PROFESSIONAL_PROFILE,
            subject="Dados profissionais inconsistentes",
            description="Solicito que a administração confira as informações exibidas.",
        )

    def test_authenticated_user_can_report_selected_profile(self):
        self.client.force_login(self.reporter)
        url = f"{reverse('moderation:report_create')}?usuario={self.target.pk}"
        response = self.client.post(
            url,
            {
                "category": ReportCategory.PROFESSIONAL_PROFILE,
                "subject": "Dados profissionais inconsistentes",
                "description": "Solicito que a administração confira as informações exibidas.",
            },
        )
        report = Report.objects.get()
        self.assertEqual(report.reporter, self.reporter)
        self.assertEqual(report.reported_user, self.target)
        self.assertEqual(report.status, ReportStatus.OPEN)
        self.assertRedirects(
            response,
            reverse("moderation:report_detail", args=(report.pk,)),
        )

    def test_user_cannot_view_another_users_report(self):
        report = self.create_report()
        self.client.force_login(self.other)
        response = self.client.get(reverse("moderation:report_detail", args=(report.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_non_admin_cannot_access_administration(self):
        self.client.force_login(self.reporter)
        response = self.client.get(reverse("moderation:admin_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_admin_review_notifies_reporter_and_creates_audit_log(self):
        report = self.create_report()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderation:admin_report_review", args=(report.pk,)),
            {
                "status": ReportStatus.RESOLVED,
                "resolution_notes": (
                    "As informações foram analisadas e as medidas cabíveis registradas."
                ),
            },
        )
        self.assertRedirects(response, reverse("moderation:admin_reports"))
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.RESOLVED)
        self.assertEqual(report.assigned_to, self.admin)
        self.assertIsNotNone(report.resolved_at)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.reporter,
                kind=NotificationKind.REPORT_UPDATE,
            ).exists()
        )
        self.assertTrue(
            AdminAuditLog.objects.filter(
                actor=self.admin,
                action=AuditAction.REPORT_REVIEW,
                target_id=report.pk,
            ).exists()
        )

    def test_admin_can_open_report_without_reported_user(self):
        report = Report.objects.create(
            reporter=self.reporter,
            category=ReportCategory.TECHNICAL,
            subject="Problema geral na plataforma",
            description="Este relato não está relacionado a uma conta específica.",
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("moderation:admin_report_review", args=(report.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Problema geral na plataforma")
        self.assertContains(response, "Não informada")

    def test_closed_report_requires_response_note(self):
        report = self.create_report()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderation:admin_report_review", args=(report.pk,)),
            {"status": ReportStatus.DISMISSED, "resolution_notes": ""},
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.OPEN)
        self.assertContains(response, "Informe um retorno antes de finalizar")
