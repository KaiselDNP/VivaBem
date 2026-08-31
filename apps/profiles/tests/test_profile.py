import shutil
import tempfile
from base64 import b64decode

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.professionals.models import ProfessionalProfile
from apps.profiles.models import UserProfile

TEST_MEDIA_ROOT = tempfile.mkdtemp()
PNG_1X1 = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="maria@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Maria",
            last_name="Silva",
            role=UserRole.SENIOR,
        )

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse("accounts:profile_edit"))
        expected = f"{reverse('accounts:login')}?next={reverse('accounts:profile_edit')}"
        self.assertRedirects(response, expected)

    def test_user_can_update_profile_and_upload_one_photo(self):
        self.client.force_login(self.user)
        photo = SimpleUploadedFile("perfil.png", PNG_1X1, content_type="image/png")

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Maria",
                "last_name": "Souza",
                "phone": "(14) 99999-9999",
                "city": "Avaré",
                "neighborhood": "Centro",
                "bio": "Gosto de conversar e participar da comunidade.",
                "photo": photo,
            },
            follow=True,
        )

        profile = UserProfile.objects.get(user=self.user)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.last_name, "Souza")
        self.assertEqual(profile.neighborhood, "Centro")
        self.assertTrue(profile.photo.name.startswith(f"profiles/{self.user.pk}/"))
        self.assertContains(response, "Perfil atualizado")

    def test_profile_photo_is_private(self):
        profile = UserProfile.objects.create(user=self.user)
        profile.photo.save(
            "perfil.png",
            SimpleUploadedFile("perfil.png", PNG_1X1, content_type="image/png"),
        )

        anonymous_response = self.client.get(reverse("accounts:profile_photo"))
        self.client.force_login(self.user)
        authenticated_response = self.client.get(reverse("accounts:profile_photo"))

        self.assertEqual(anonymous_response.status_code, 302)
        self.assertEqual(authenticated_response.status_code, 200)
        self.assertEqual(authenticated_response["Content-Type"], "image/png")
        self.assertIn("no-store", authenticated_response["Cache-Control"])

    def test_app_header_uses_current_profile_photo(self):
        profile = UserProfile.objects.create(user=self.user)
        profile.photo.save(
            "perfil.png",
            SimpleUploadedFile("perfil.png", PNG_1X1, content_type="image/png"),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:dashboard"))

        photo_url = reverse("accounts:profile_photo")
        self.assertContains(response, f'src="{photo_url}?v=')
        self.assertContains(response, "dashboard-welcome-avatar")
        self.assertNotContains(response, "avatar avatar-small avatar-initials")

    def test_user_can_remove_current_photo(self):
        profile = UserProfile.objects.create(user=self.user, city="Avaré")
        profile.photo.save(
            "perfil.png",
            SimpleUploadedFile("perfil.png", PNG_1X1, content_type="image/png"),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Maria",
                "last_name": "Silva",
                "city": "Avaré",
                "remove_photo": "on",
            },
        )

        profile.refresh_from_db()
        self.assertRedirects(response, reverse("accounts:profile_edit"))
        self.assertFalse(profile.photo)

    def test_professional_photo_is_saved_even_if_professional_fields_need_correction(self):
        professional = get_user_model().objects.create_user(
            email="pablo@example.com",
            password="UmaSenhaBemSegura123!",
            first_name="Pablo",
            role=UserRole.PROFESSIONAL,
        )
        ProfessionalProfile.objects.create(
            user=professional,
            profession="",
            specialty="",
        )
        photo = SimpleUploadedFile("pablo.png", PNG_1X1, content_type="image/png")
        self.client.force_login(professional)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Pablo",
                "last_name": "Anconi",
                "city": "Avaré",
                "photo": photo,
                "profession": "",
                "specialty": "",
                "council": "",
                "registration_number": "",
                "service_region": "Avaré-SP",
                "service_mode": "both",
            },
        )

        profile = UserProfile.objects.get(user=professional)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(profile.photo.name.startswith(f"profiles/{professional.pk}/"))
        self.assertContains(response, "Sua foto e seus dados pessoais foram salvos")
        self.assertContains(response, "Este campo é obrigatório")
