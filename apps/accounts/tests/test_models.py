from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import UserRole


class UserManagerTests(TestCase):
    def test_create_user_uses_email_and_hashes_password(self):
        user = get_user_model().objects.create_user(
            email="IDOSO@EXEMPLO.COM",
            password="senha-segura-de-teste",
            role=UserRole.SENIOR,
        )

        self.assertEqual(user.email, "idoso@exemplo.com")
        self.assertTrue(user.check_password("senha-segura-de-teste"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_assigns_admin_role(self):
        user = get_user_model().objects.create_superuser(
            email="admin@vivabem.local",
            password="senha-segura-de-teste",
        )

        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
