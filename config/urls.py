from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Administração VivaBem"
admin.site.site_title = "VivaBem"
admin.site.index_title = "Gestão da plataforma"
admin.site.site_url = "/painel/"
admin.site.empty_value_display = "—"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("necessidades/", include("apps.needs.urls")),
    path("vinculos/", include("apps.relationships.urls")),
    path("profissionais/", include("apps.professionals.urls")),
    path("notificacoes/", include("apps.notifications.urls")),
    path("", include("apps.moderation.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
]
