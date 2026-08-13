from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole


class SignUpFlowTests(TestCase):
    password = "UmaSenhaBemSegura123!"

    def signup_data(self, **overrides):
        data = {
            "first_name": "Maria",
            "last_name": "Silva",
            "email": "maria@example.com",
            "password1": self.password,
            "password2": self.password,
            "accepted_privacy": "on",
        }
        data.update(overrides)
        return data

    def test_senior_can_register_and_is_logged_in(self):
        response = self.client.post(
            reverse("accounts:signup_senior"), self.signup_data(), follow=True
        )

        user = get_user_model().objects.get(email="maria@example.com")
        self.assertEqual(user.role, UserRole.SENIOR)
        self.assertIsNotNone(user.accepted_terms_at)
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertContains(response, "Seu cadastro de pessoa idosa está ativo")

    def test_family_can_register(self):
        response = self.client.post(
            reverse("accounts:signup_family"), self.signup_data(email="ana@example.com")
        )

        user = get_user_model().objects.get(email="ana@example.com")
        self.assertEqual(user.role, UserRole.FAMILY)
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_role_cannot_be_escalated_through_post_data(self):
        self.client.post(
            reverse("accounts:signup_senior"),
            self.signup_data(email="seguro@example.com", role=UserRole.ADMIN),
        )

        user = get_user_model().objects.get(email="seguro@example.com")
        self.assertEqual(user.role, UserRole.SENIOR)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_privacy_acceptance_is_required(self):
        data = self.signup_data()
        data.pop("accepted_privacy")

        response = self.client.post(reverse("accounts:signup_senior"), data)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "accepted_privacy",
            "Você precisa aceitar o aviso de privacidade.",
        )
        self.assertFalse(get_user_model().objects.exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        get_user_model().objects.create_user(
            email="maria@example.com", password=self.password, role=UserRole.SENIOR
        )

        response = self.client.post(
            reverse("accounts:signup_family"), self.signup_data(email="MARIA@EXAMPLE.COM")
        )

        self.assertFormError(
            response.context["form"], "email", "Já existe uma conta com este e-mail."
        )
        self.assertEqual(get_user_model().objects.count(), 1)


class LoginAndAccessTests(TestCase):
    password = "UmaSenhaBemSegura123!"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="familiar@example.com",
            password=self.password,
            first_name="Carlos",
            role=UserRole.FAMILY,
        )

    def test_user_can_log_in_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "FAMILIAR@EXAMPLE.COM", "password": self.password},
        )

        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_dashboard_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("accounts:dashboard"))

        expected = f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}"
        self.assertRedirects(response, expected)

    def test_dashboard_shows_logout_button(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertContains(response, reverse("accounts:logout"))
        self.assertContains(response, "Sair</button>")

    def test_logout_requires_post_and_ends_session(self):
        self.client.force_login(self.user)

        get_response = self.client.get(reverse("accounts:logout"))
        post_response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)
