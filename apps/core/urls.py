from django.urls import path

from .views import HelpView, HomeView, PrivacyView, health_check

app_name = "core"

urlpatterns = [
    path("status/", health_check, name="health_check"),
    path("", HomeView.as_view(), name="home"),
    path("ajuda/", HelpView.as_view(), name="help"),
    path("privacidade/", PrivacyView.as_view(), name="privacy"),
]
