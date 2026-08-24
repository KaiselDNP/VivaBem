from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.conversation_list, name="list"),
    path("iniciar/<int:user_id>/", views.conversation_start, name="start"),
    path("<int:pk>/mensagens/", views.conversation_messages, name="messages"),
    path("<int:pk>/bloquear/", views.conversation_block, name="block"),
    path("<int:pk>/desbloquear/", views.conversation_unblock, name="unblock"),
    path("<int:pk>/", views.conversation_detail, name="detail"),
]
