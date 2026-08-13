from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import UserRole


class BootstrapAdminCommandTests(TestCase):
    def test_command_skips_when_environment_is_not_configured(self):
        output = StringIO()
        with patch.dict(
            "os.environ",
            {"VIVABEM_ADMIN_EMAIL": "", "VIVABEM_ADMIN_PASSWORD": ""},
        ):
            call_command("bootstrap_admin", stdout=output)

        self.assertFalse(get_user_model().objects.exists())
        self.assertIn("etapa ignorada", output.getvalue())

    def test_command_creates_admin_without_exposing_password(self):
        output = StringIO()
        password = "SenhaAdministrativaMuitoSegura987!"
        with patch.dict(
            "os.environ",
            {
                "VIVABEM_ADMIN_EMAIL": "ADMIN@EXAMPLE.COM",
                "VIVABEM_ADMIN_PASSWORD": password,
            },
        ):
            call_command("bootstrap_admin", stdout=output)

        user = get_user_model().objects.get(email="admin@example.com")
        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password(password))
        self.assertNotIn(password, output.getvalue())
