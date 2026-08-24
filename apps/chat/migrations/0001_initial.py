import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizada em")),
                ("participant_one", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_conversations_as_first", to=settings.AUTH_USER_MODEL, verbose_name="primeiro participante")),
                ("participant_two", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_conversations_as_second", to=settings.AUTH_USER_MODEL, verbose_name="segundo participante")),
            ],
            options={"verbose_name": "conversa", "verbose_name_plural": "conversas", "ordering": ("-updated_at",)},
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(max_length=1000, verbose_name="mensagem")),
                ("read_at", models.DateTimeField(blank=True, null=True, verbose_name="lida em")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="enviada em")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_messages_sent", to=settings.AUTH_USER_MODEL, verbose_name="remetente")),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="chat.conversation", verbose_name="conversa")),
            ],
            options={"verbose_name": "mensagem", "verbose_name_plural": "mensagens", "ordering": ("created_at",)},
        ),
        migrations.AddConstraint(model_name="conversation", constraint=models.UniqueConstraint(fields=("participant_one", "participant_two"), name="chat_unique_participant_pair")),
        migrations.AddConstraint(model_name="conversation", constraint=models.CheckConstraint(condition=models.Q(("participant_one_id__lt", models.F("participant_two_id"))), name="chat_participants_canonical_order")),
        migrations.AddIndex(model_name="chatmessage", index=models.Index(fields=["conversation", "created_at"], name="chat_chatme_convers_c2caf0_idx")),
        migrations.AddIndex(model_name="chatmessage", index=models.Index(fields=["conversation", "read_at"], name="chat_chatme_convers_eee83e_idx")),
    ]
