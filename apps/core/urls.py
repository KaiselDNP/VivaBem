from django.urls import path

from .views import HomeView, PrivacyView, health_check

app_name = "core"

urlpatterns = [
    path("status/", health_check, name="health_check"),
    path("", HomeView.as_view(), name="home"),
    path("privacidade/", PrivacyView.as_view(), name="privacy"),
]
