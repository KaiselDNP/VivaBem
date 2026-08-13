from django.urls import path

from . import views

app_name = "relationships"

urlpatterns = [
    path("", views.link_list, name="list"),
    path("solicitar/", views.request_link, name="request"),
    path("<int:pk>/responder/<str:action>/", views.respond_link, name="respond"),
    path("<int:pk>/permissoes/", views.edit_permissions, name="permissions"),
    path("<int:pk>/revogar/", views.revoke_link, name="revoke"),
    path("<int:pk>/acompanhar/", views.senior_overview, name="senior_overview"),
]
