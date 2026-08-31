from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.needs.models import HelpRequest, Need, NeedCategory


class SeniorDashboardSimplicityTests(TestCase):
    def setUp(self):
        self.senior = get_user_model().objects.create_user(
            email="senior-dashboard@example.com",
            password="FraseSegura123!",
            first_name="Maria",
            role=UserRole.SENIOR,
        )
        self.client.force_login(self.senior)

    def test_main_page_prioritizes_three_plain_actions(self):
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertContains(response, "O que você quer fazer hoje?")
        self.assertContains(response, "Pedir ajuda")
        self.assertContains(response, "Acompanhar pedidos")
        self.assertContains(response, "Conversar")
        self.assertContains(response, "Outras opções")
        self.assertNotContains(response, "Ajuda que cadastrei")
        self.assertNotContains(response, "Conta ativa")
        self.assertNotContains(response, "Seu último pedido")
        self.assertNotContains(response, "data-reading-welcome")

    def test_only_latest_request_is_shown(self):
        older_need = Need.objects.create(
            senior=self.senior,
            title="Pedido antigo",
            category=NeedCategory.DIGITAL,
            description="Primeiro pedido.",
        )
        HelpRequest.objects.create(need=older_need, details="Primeiro pedido.")
        latest_need = Need.objects.create(
            senior=self.senior,
            title="Pedido mais recente",
            category=NeedCategory.COMPANIONSHIP,
            description="Segundo pedido.",
        )
        HelpRequest.objects.create(need=latest_need, details="Segundo pedido.")

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertContains(response, "Seu último pedido")
        self.assertContains(response, "Pedido mais recente")
        self.assertNotContains(response, "Pedido antigo")
