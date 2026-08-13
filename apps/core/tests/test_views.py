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
