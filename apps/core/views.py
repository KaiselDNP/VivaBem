from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/home.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


class HelpView(TemplateView):
    template_name = "core/help.html"


def health_check(request):
    return HttpResponse("ok", content_type="text/plain")


def readiness_check(request):
    """Confirm that the application can answer and reach its database."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse(
            {"status": "indisponivel", "database": "erro"},
            status=503,
        )
    return JsonResponse({"status": "ok", "database": "ok"})
