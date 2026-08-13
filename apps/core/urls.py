from django.urls import path

from .views import HomeView, PrivacyView

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("privacidade/", PrivacyView.as_view(), name="privacy"),
]
