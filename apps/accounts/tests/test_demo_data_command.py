import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.accounts.models import UserRole
from apps.needs.models import HelpRequest, ProfessionalInterest
from apps.relationships.models import FamilyLink, FamilyPermission


class DemoDataCommandTests(TestCase):
    password = "SenhaFicticia2026!"

    @override_settings(DEBUG=True)
    @patch.dict(os.environ, {"VIVABEM_DEMO_PASSWORD": password})
    def test_command_creates_reusable_demo_scenario(self):
        call_command("seed_demo_data")
        call_command("seed_demo_data")

        users = get_user_model().objects.filter(email__endswith="@demo.vivabem.test")
        admin = users.get(role=UserRole.ADMIN)
        self.assertEqual(users.count(), 4)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password(self.password))
        self.assertEqual(FamilyLink.objects.count(), 1)
        self.assertEqual(FamilyPermission.objects.count(), 1)
        self.assertEqual(HelpRequest.objects.count(), 1)
        self.assertEqual(ProfessionalInterest.objects.count(), 1)

    @override_settings(DEBUG=False)
    def test_command_refuses_to_run_outside_debug_mode(self):
        with self.assertRaisesMessage(CommandError, "DEBUG=true"):
            call_command("seed_demo_data")
