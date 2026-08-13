from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole

from ..models import ProfessionalProfile


class ProfessionalDirectoryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.viewer = user_model.objects.create_user(
            email="idoso@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.SENIOR,
        )
        matching_user = user_model.objects.create_user(
            email="ana@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Ana",
            role=UserRole.PROFESSIONAL,
        )
        ProfessionalProfile.objects.create(
            user=matching_user,
            profession="Terapeuta ocupacional",
            specialty="Tecnologia assistiva",
            service_region="Avaré-SP",
        )
        other_user = user_model.objects.create_user(
            email="bruno@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Bruno",
            role=UserRole.PROFESSIONAL,
        )
        ProfessionalProfile.objects.create(
            user=other_user,
            profession="Psicólogo",
            specialty="Acolhimento",
            service_region="Botucatu-SP",
        )

    def test_search_filters_professionals_without_exposing_email(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("professionals:directory"), {"q": "Tecnologia"})
        self.assertContains(response, "Ana")
        self.assertNotContains(response, "Bruno")
        self.assertNotContains(response, "ana@example.com")
