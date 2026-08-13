from django.http import HttpResponse
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/home.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


def health_check(request):
    return HttpResponse("ok", content_type="text/plain")
