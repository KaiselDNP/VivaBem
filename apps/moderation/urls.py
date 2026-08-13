from django.urls import path

from . import views

app_name = "moderation"

urlpatterns = [
    path("denuncias/", views.report_list, name="report_list"),
    path("denuncias/nova/", views.report_create, name="report_create"),
    path("denuncias/<int:pk>/", views.report_detail, name="report_detail"),
    path("gestao/", views.administration_dashboard, name="admin_dashboard"),
    path("gestao/denuncias/", views.administration_reports, name="admin_reports"),
    path(
        "gestao/denuncias/<int:pk>/",
        views.administration_report_review,
        name="admin_report_review",
    ),
    path(
        "gestao/profissionais/",
        views.administration_professionals,
        name="admin_professionals",
    ),
    path(
        "gestao/profissionais/<int:pk>/",
        views.administration_professional_review,
        name="admin_professional_review",
    ),
    path("gestao/usuarios/", views.administration_users, name="admin_users"),
    path("gestao/avisos/", views.administration_announcements, name="admin_announcements"),
    path(
        "gestao/avisos/novo/",
        views.administration_announcement_create,
        name="admin_announcement_create",
    ),
    path(
        "gestao/usuarios/<int:pk>/<str:action>/",
        views.administration_user_status,
        name="admin_user_status",
    ),
    path("gestao/auditoria/", views.administration_audit, name="admin_audit"),
]
