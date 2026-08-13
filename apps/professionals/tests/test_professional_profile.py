from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.profiles.models import UserProfile

from ..models import ProfessionalProfile, ServiceMode, VerificationStatus


class ProfessionalSignUpTests(TestCase):
    def test_professional_can_register_and_is_sent_to_profile(self):
        response = self.client.post(
            reverse("accounts:signup_professional"),
            {
                "first_name": "João",
                "last_name": "Santos",
                "email": "joao@example.com",
                "password1": "UmaSenhaBemSegura123!",
                "password2": "UmaSenhaBemSegura123!",
                "accepted_privacy": "on",
            },
        )

        user = get_user_model().objects.get(email="joao@example.com")
        self.assertEqual(user.role, UserRole.PROFESSIONAL)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(ProfessionalProfile.objects.filter(user=user).exists())
        self.assertRedirects(response, reverse("accounts:profile_edit"))


class ProfessionalProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="profissional@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Ana",
            last_name="Lima",
            role=UserRole.PROFESSIONAL,
        )
        UserProfile.objects.create(user=self.user)
        self.professional = ProfessionalProfile.objects.create(user=self.user)
        self.client.force_login(self.user)

    def profile_data(self, **overrides):
        data = {
            "first_name": "Ana",
            "last_name": "Lima",
            "city": "Avaré",
            "profession": "Fisioterapeuta",
            "specialty": "Gerontologia",
            "council": "CREFITO",
            "registration_number": "12345-SP",
            "service_region": "Avaré-SP e região",
            "service_mode": ServiceMode.BOTH,
        }
        data.update(overrides)
        return data

    def test_professional_can_update_own_professional_data(self):
        response = self.client.post(
            reverse("accounts:profile_edit"), self.profile_data(), follow=True
        )

        self.professional.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.professional.profession, "Fisioterapeuta")
        self.assertEqual(self.professional.registration_number, "12345-SP")
        self.assertEqual(self.professional.verification_status, VerificationStatus.PENDING)
        self.assertContains(response, "Dados profissionais")

    def test_user_cannot_set_verified_status_through_profile_form(self):
        self.client.post(
            reverse("accounts:profile_edit"),
            self.profile_data(
                verification_status=VerificationStatus.VERIFIED,
                verified_by=self.user.pk,
            ),
        )

        self.professional.refresh_from_db()
        self.assertEqual(self.professional.verification_status, VerificationStatus.PENDING)
        self.assertIsNone(self.professional.verified_by)

    def test_editing_verified_credentials_returns_status_to_pending(self):
        self.professional.profession = "Fisioterapeuta"
        self.professional.specialty = "Gerontologia"
        self.professional.service_region = "Avaré-SP"
        self.professional.verification_status = VerificationStatus.VERIFIED
        self.professional.verified_at = timezone.now()
        self.professional.verified_by = self.user
        self.professional.save()

        self.client.post(
            reverse("accounts:profile_edit"),
            self.profile_data(specialty="Saúde da pessoa idosa"),
        )

        self.professional.refresh_from_db()
        self.assertEqual(self.professional.verification_status, VerificationStatus.PENDING)
        self.assertIsNone(self.professional.verified_at)
        self.assertIsNone(self.professional.verified_by)

    def test_non_professional_does_not_receive_professional_form(self):
        family = get_user_model().objects.create_user(
            email="familiar2@example.com",
            password="UmaSenhaBemSegura123!",
            role=UserRole.FAMILY,
        )
        self.client.force_login(family)

        response = self.client.get(reverse("accounts:profile_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Dados profissionais")
