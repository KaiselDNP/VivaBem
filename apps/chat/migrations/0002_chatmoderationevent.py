import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(
        name="ChatModerationEvent",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("matched_categories", models.CharField(max_length=120, verbose_name="categorias detectadas")),
            ("message_length", models.PositiveIntegerField(verbose_name="tamanho da mensagem")),
            ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="registrado em")),
            ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_events", to="chat.conversation", verbose_name="conversa")),
            ("recipient", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="chat_moderation_events_received", to=settings.AUTH_USER_MODEL, verbose_name="destinatário")),
            ("sender", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="chat_moderation_events_sent", to=settings.AUTH_USER_MODEL, verbose_name="remetente")),
        ],
        options={"verbose_name": "evento de moderação do chat", "verbose_name_plural": "eventos de moderação do chat", "ordering": ("-created_at",)},
    )]
