import re
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
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
        cache.clear()
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

    @override_settings(LOGIN_MAX_ATTEMPTS=3, LOGIN_LOCKOUT_SECONDS=60)
    def test_repeated_invalid_logins_are_temporarily_limited(self):
        for _ in range(3):
            response = self.client.post(
                reverse("accounts:login"),
                {"username": self.user.email, "password": "senha-incorreta"},
            )
            self.assertEqual(response.status_code, 200)

        blocked = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": self.password},
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertContains(blocked, "Muitas tentativas", status_code=429)
        self.assertNotIn("_auth_user_id", self.client.session)

        cache.clear()
        allowed = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": self.password},
        )
        self.assertRedirects(allowed, reverse("accounts:dashboard"))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetFlowTests(TestCase):
    old_password = "UmaSenhaBemSegura123!"
    new_password = "OutraSenhaAindaMaisSegura456!"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="recuperar@example.com",
            password=self.old_password,
            first_name="Helena",
            role=UserRole.SENIOR,
        )

    def test_login_page_offers_password_recovery(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertContains(response, reverse("accounts:password_reset"))
        self.assertContains(response, "Esqueci minha senha")

    def test_unknown_email_receives_same_response_without_sending_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "nao-cadastrado@example.com"},
        )

        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_active_user_can_reset_password_with_single_use_link(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.user.email.upper()},
        )

        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(self.old_password, mail.outbox[0].body)

        match = re.search(r"http://testserver(?P<path>/redefinir-senha/\S+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        token_path = urlsplit(match.group("path")).path

        token_response = self.client.get(token_path)
        self.assertEqual(token_response.status_code, 302)
        set_password_url = token_response.url

        form_response = self.client.get(set_password_url)
        self.assertContains(form_response, "Crie uma nova senha")

        complete = self.client.post(
            set_password_url,
            {
                "new_password1": self.new_password,
                "new_password2": self.new_password,
            },
        )
        self.assertRedirects(complete, reverse("accounts:password_reset_complete"))

        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(self.old_password))
        self.assertTrue(self.user.check_password(self.new_password))

        reused = self.client.get(token_path, follow=True)
        self.assertContains(reused, "Este link não é mais válido")
