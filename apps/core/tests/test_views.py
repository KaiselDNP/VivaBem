from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    def test_health_check_is_public(self):
        response = self.client.get(reverse("core:health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_home_page_is_public_and_explains_scope(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cuidado conectado, com respeito e autonomia")
        self.assertContains(response, "não substitui")
        self.assertContains(response, "serviços ou profissionais de saúde")
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, "/static/js/theme.js")
        self.assertContains(response, "data-font-size-select")
        self.assertContains(response, "Pequena")
        self.assertContains(response, "Média")
        self.assertContains(response, "Grande")
        self.assertContains(response, "Super grande")
        self.assertContains(response, 'aria-keyshortcuts="F2"')
        self.assertContains(response, "data-read-aloud")
        self.assertContains(response, "/static/js/accessibility.js")
        self.assertContains(response, "data-reading-welcome")
        self.assertContains(response, "Você prefere letras bem grandes?")
        self.assertContains(response, 'data-reading-choice="xlarge"')
        self.assertContains(response, 'data-reading-choice="medium"')

    def test_help_page_is_public_and_uses_simple_instructions(self):
        response = self.client.get(reverse("core:help"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Como podemos ajudar?")
        self.assertContains(response, "Ouvir um item")
        self.assertContains(response, "F2")
        self.assertContains(response, "data-read-selection-prompt")
        self.assertContains(response, "SAMU")
        self.assertContains(response, "192")
