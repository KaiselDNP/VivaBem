from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.notifications.models import Notification
from apps.professionals.models import ProfessionalProfile, ServiceMode

from ..models import (
    HelpRequest,
    HelpRequestStatus,
    InterestStatus,
    Need,
    NeedCategory,
    ProfessionalInterest,
)


class NeedAndRequestFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.senior = user_model.objects.create_user(
            email="maria@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Maria",
            role=UserRole.SENIOR,
        )
        self.other_senior = user_model.objects.create_user(
            email="outra@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.SENIOR,
        )
        self.professional = user_model.objects.create_user(
            email="profissional@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Ana",
            role=UserRole.PROFESSIONAL,
        )
        self.professional_profile = ProfessionalProfile.objects.create(
            user=self.professional,
            profession="Terapeuta ocupacional",
            specialty="Apoio à autonomia",
            service_region="Avaré-SP",
            service_mode=ServiceMode.BOTH,
        )
        self.need = Need.objects.create(
            senior=self.senior,
            title="Ajuda com celular",
            category=NeedCategory.DIGITAL,
            description="Preciso aprender a usar chamadas de vídeo.",
        )
        self.help_request = HelpRequest.objects.create(
            need=self.need,
            details="Gostaria de apoio para configurar o aplicativo.",
            region="Avaré-SP",
        )

    def test_senior_can_create_need_but_professional_cannot(self):
        self.client.force_login(self.senior)
        response = self.client.post(
            reverse("needs:create"),
            {
                "title": "Companhia para caminhada",
                "category": NeedCategory.COMPANIONSHIP,
                "description": "Procuro companhia para uma atividade social.",
            },
        )
        self.assertRedirects(response, reverse("needs:list"))
        self.assertTrue(
            Need.objects.filter(senior=self.senior, title="Companhia para caminhada").exists()
        )

        self.client.force_login(self.professional)
        denied = self.client.post(
            reverse("needs:create"),
            {
                "title": "Não autorizado",
                "category": NeedCategory.OTHER,
                "description": "Este registro não deve ser criado.",
            },
        )
        self.assertEqual(denied.status_code, 403)
        self.assertFalse(Need.objects.filter(title="Não autorizado").exists())

    def test_other_senior_cannot_view_request(self):
        self.client.force_login(self.other_senior)
        response = self.client.get(reverse("needs:request_detail", args=(self.help_request.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_request_form_is_guided_and_senior_without_need_starts_with_simple_step(self):
        self.client.force_login(self.senior)
        guided_response = self.client.get(reverse("needs:request_create"))

        self.assertContains(guided_response, "data-guided-form")
        self.assertContains(guided_response, "Etapa 1 de 5")
        self.assertContains(guided_response, "Escolher o que ouvir")

        self.client.force_login(self.other_senior)
        first_step = self.client.get(reverse("needs:request_create"))

        self.assertRedirects(
            first_step,
            f"{reverse('needs:create')}?continuar=pedido",
        )

    def test_senior_creates_request_only_for_own_need(self):
        another_need = Need.objects.create(
            senior=self.other_senior,
            title="Necessidade de outra pessoa",
            category=NeedCategory.OTHER,
            description="Registro pertencente a outra conta.",
        )
        self.client.force_login(self.senior)
        response = self.client.post(
            reverse("needs:request_create"),
            {
                "need": self.need.pk,
                "details": "Preciso de ajuda na próxima semana.",
                "region": "Avaré-SP",
                "priority": "soon",
                "preferred_service_mode": ServiceMode.BOTH,
            },
        )
        created = HelpRequest.objects.exclude(pk=self.help_request.pk).get()
        self.assertRedirects(
            response,
            reverse("needs:request_detail", args=(created.pk,)),
        )

        denied = self.client.post(
            reverse("needs:request_create"),
            {
                "need": another_need.pk,
                "details": "Tentativa indevida.",
                "region": "Avaré-SP",
                "priority": "routine",
                "preferred_service_mode": ServiceMode.BOTH,
            },
        )
        self.assertEqual(denied.status_code, 200)
        self.assertFalse(HelpRequest.objects.filter(need=another_need).exists())

    def test_professional_sees_opportunity_without_senior_identity_and_sends_interest(self):
        self.client.force_login(self.professional)
        response = self.client.get(reverse("needs:opportunities"))
        self.assertContains(response, self.need.title)
        self.assertNotContains(response, self.senior.email)
        self.assertNotContains(response, self.senior.first_name)

        response = self.client.post(
            reverse("needs:interest", args=(self.help_request.pk,)),
            {"message": "Posso orientar o uso do aplicativo com calma."},
        )
        self.assertRedirects(response, reverse("needs:opportunities"))
        self.assertTrue(
            ProfessionalInterest.objects.filter(
                help_request=self.help_request,
                professional=self.professional,
                status=InterestStatus.PENDING,
            ).exists()
        )
        self.assertTrue(Notification.objects.filter(recipient=self.senior).exists())

    def test_only_owner_accepts_interest_and_can_complete_request(self):
        interest = ProfessionalInterest.objects.create(
            help_request=self.help_request,
            professional=self.professional,
            message="Tenho disponibilidade.",
        )
        accept_url = reverse(
            "needs:respond_interest",
            args=(self.help_request.pk, interest.pk, "accept"),
        )

        self.client.force_login(self.other_senior)
        self.assertEqual(self.client.post(accept_url).status_code, 404)

        self.client.force_login(self.senior)
        response = self.client.post(accept_url)
        self.assertRedirects(
            response,
            reverse("needs:request_detail", args=(self.help_request.pk,)),
        )
        interest.refresh_from_db()
        self.help_request.refresh_from_db()
        self.assertEqual(interest.status, InterestStatus.ACCEPTED)
        self.assertEqual(self.help_request.status, HelpRequestStatus.ACCEPTED)

        complete_url = reverse("needs:request_status", args=(self.help_request.pk, "complete"))
        self.client.post(complete_url)
        self.help_request.refresh_from_db()
        self.assertEqual(self.help_request.status, HelpRequestStatus.COMPLETED)
