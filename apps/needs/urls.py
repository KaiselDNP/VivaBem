from django.urls import path

from . import views

app_name = "needs"

urlpatterns = [
    path("", views.need_list, name="list"),
    path("nova/", views.need_create, name="create"),
    path("<int:pk>/editar/", views.need_edit, name="edit"),
    path("<int:pk>/resolver/", views.need_resolve, name="resolve"),
    path("solicitacoes/", views.request_list, name="request_list"),
    path("solicitacoes/nova/", views.request_create, name="request_create"),
    path("solicitacoes/<int:pk>/", views.request_detail, name="request_detail"),
    path(
        "solicitacoes/<int:pk>/status/<str:action>/",
        views.request_status,
        name="request_status",
    ),
    path("oportunidades/", views.opportunities, name="opportunities"),
    path("oportunidades/<int:pk>/interesse/", views.express_interest, name="interest"),
    path(
        "solicitacoes/<int:request_pk>/interesses/<int:interest_pk>/<str:action>/",
        views.respond_interest,
        name="respond_interest",
    ),
]
