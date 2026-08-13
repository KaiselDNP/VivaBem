from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.profiles.views import ProfileEditView, profile_photo

from .views import (
    DashboardView,
    FamilySignUpView,
    ProfessionalSignUpView,
    SeniorSignUpView,
    SignUpChoiceView,
    VivaBemLoginView,
    VivaBemPasswordResetCompleteView,
    VivaBemPasswordResetConfirmView,
    VivaBemPasswordResetDoneView,
    VivaBemPasswordResetView,
)

app_name = "accounts"

urlpatterns = [
    path("entrar/", VivaBemLoginView.as_view(), name="login"),
    path("recuperar-acesso/", VivaBemPasswordResetView.as_view(), name="password_reset"),
    path(
        "recuperar-acesso/enviado/",
        VivaBemPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "redefinir-senha/<uidb64>/<token>/",
        VivaBemPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "redefinir-senha/concluido/",
        VivaBemPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("sair/", LogoutView.as_view(), name="logout"),
    path("cadastro/", SignUpChoiceView.as_view(), name="signup_choice"),
    path("cadastro/idoso/", SeniorSignUpView.as_view(), name="signup_senior"),
    path("cadastro/familiar/", FamilySignUpView.as_view(), name="signup_family"),
    path(
        "cadastro/profissional/",
        ProfessionalSignUpView.as_view(),
        name="signup_professional",
    ),
    path("painel/", DashboardView.as_view(), name="dashboard"),
    path("perfil/", ProfileEditView.as_view(), name="profile_edit"),
    path("perfil/foto/", profile_photo, name="profile_photo"),
]
