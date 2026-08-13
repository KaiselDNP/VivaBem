from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.needs.models import HelpRequest, Need, NeedCategory
from apps.notifications.models import Notification, NotificationKind
from apps.relationships.models import FamilyLink, FamilyLinkStatus


class SecurityHeaderTests(TestCase):
    def test_public_response_has_browser_security_headers(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
        self.assertEqual(response.headers["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertEqual(
            response.headers["Permissions-Policy"],
            "camera=(), microphone=(), geolocation=()",
        )


class FinalPermissionFlowTests(TestCase):
    password = "UmaSenhaBemSegura123!"

    def setUp(self):
        users = get_user_model().objects
        self.senior = users.create_user(
            email="idosa@example.com",
            password=self.password,
            first_name="Maria",
            role=UserRole.SENIOR,
        )
        self.other_senior = users.create_user(
            email="outra-idosa@example.com",
            password=self.password,
            role=UserRole.SENIOR,
        )
        self.family = users.create_user(
            email="familiar@example.com",
            password=self.password,
            role=UserRole.FAMILY,
        )
        self.other_family = users.create_user(
            email="outro-familiar@example.com",
            password=self.password,
            role=UserRole.FAMILY,
        )
        self.professional = users.create_user(
            email="profissional@example.com",
            password=self.password,
            role=UserRole.PROFESSIONAL,
        )
        self.admin = users.create_user(
            email="admin@example.com",
            password=self.password,
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.need = Need.objects.create(
            senior=self.senior,
            title="Apoio digital",
            category=NeedCategory.DIGITAL,
            description="Ajuda para utilizar chamada de vídeo.",
        )
        self.help_request = HelpRequest.objects.create(
            need=self.need,
            details="Configurar o aplicativo de chamada.",
        )
        self.link = FamilyLink.objects.create(
            senior=self.senior,
            family=self.family,
            requested_by=self.family,
            status=FamilyLinkStatus.APPROVED,
        )
        self.notification = Notification.objects.create(
            recipient=self.senior,
            kind=NotificationKind.ADMIN_NOTICE,
            title="Aviso privado",
            message="Mensagem destinada somente à pessoa idosa.",
        )

    def test_anonymous_user_is_redirected_from_all_private_areas(self):
        private_urls = (
            reverse("accounts:dashboard"),
            reverse("accounts:profile_edit"),
            reverse("needs:list"),
            reverse("needs:request_list"),
            reverse("needs:opportunities"),
            reverse("relationships:list"),
            reverse("professionals:directory"),
            reverse("notifications:list"),
            reverse("moderation:report_list"),
            reverse("moderation:admin_dashboard"),
        )

        for url in private_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_role_specific_areas_reject_other_profiles(self):
        matrix = (
            (self.family, reverse("needs:list"), 403),
            (self.professional, reverse("needs:list"), 403),
            (self.senior, reverse("needs:opportunities"), 403),
            (self.family, reverse("needs:opportunities"), 403),
            (self.professional, reverse("relationships:list"), 403),
            (self.family, reverse("moderation:admin_dashboard"), 403),
            (self.admin, reverse("moderation:admin_dashboard"), 200),
        )

        for user, url, expected_status in matrix:
            with self.subTest(user=user.email, url=url):
                self.client.force_login(user)
                self.assertEqual(self.client.get(url).status_code, expected_status)
                self.client.logout()

    def test_objects_cannot_be_accessed_by_changing_the_url_identifier(self):
        self.client.force_login(self.other_senior)
        self.assertEqual(
            self.client.get(reverse("needs:edit", args=(self.need.pk,))).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                reverse("needs:request_detail", args=(self.help_request.pk,))
            ).status_code,
            404,
        )

        self.client.force_login(self.other_family)
        self.assertEqual(
            self.client.get(
                reverse("relationships:senior_overview", args=(self.link.pk,))
            ).status_code,
            404,
        )

        self.client.force_login(self.family)
        self.assertEqual(
            self.client.post(
                reverse("notifications:mark_read", args=(self.notification.pk,))
            ).status_code,
            404,
        )

    def test_sensitive_changes_reject_get_requests(self):
        self.client.force_login(self.senior)
        senior_mutations = (
            reverse("needs:resolve", args=(self.need.pk,)),
            reverse("needs:request_status", args=(self.help_request.pk, "cancel")),
            reverse("relationships:respond", args=(self.link.pk, "approve")),
            reverse("relationships:revoke", args=(self.link.pk,)),
            reverse("notifications:mark_read", args=(self.notification.pk,)),
            reverse("notifications:mark_all_read"),
        )
        for url in senior_mutations:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

        self.client.force_login(self.admin)
        admin_status_url = reverse(
            "moderation:admin_user_status",
            args=(self.family.pk, "deactivate"),
        )
        self.assertEqual(self.client.get(admin_status_url).status_code, 405)

    def test_sensitive_post_without_csrf_token_is_rejected(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.senior)

        response = csrf_client.post(reverse("needs:resolve", args=(self.need.pk,)))

        self.assertEqual(response.status_code, 403)
        self.need.refresh_from_db()
        self.assertEqual(self.need.status, "active")

    def test_revoked_family_link_no_longer_grants_access(self):
        self.link.status = FamilyLinkStatus.REVOKED
        self.link.save(update_fields=("status",))
        self.client.force_login(self.family)

        response = self.client.get(reverse("relationships:senior_overview", args=(self.link.pk,)))

        self.assertEqual(response.status_code, 404)

    def test_authenticated_user_can_find_privacy_request_channel(self):
        self.client.force_login(self.family)

        response = self.client.get(reverse("core:privacy"))

        self.assertContains(response, reverse("moderation:report_create"))
        self.assertContains(response, "solicitação sobre privacidade")

    def test_private_pages_are_not_stored_in_browser_cache(self):
        self.client.force_login(self.family)

        response = self.client.get(reverse("accounts:dashboard"))

        cache_control = response.headers["Cache-Control"]
        self.assertIn("private", cache_control)
        self.assertIn("no-store", cache_control)
