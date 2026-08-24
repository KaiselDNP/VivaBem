import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0002_chatmoderationevent"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(
        name="ChatBlock",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="bloqueado em")),
            ("blocked", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_blocks_received", to=settings.AUTH_USER_MODEL, verbose_name="conta bloqueada")),
            ("blocker", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_blocks_created", to=settings.AUTH_USER_MODEL, verbose_name="quem bloqueou")),
        ],
        options={
            "verbose_name": "bloqueio de chat",
            "verbose_name_plural": "bloqueios de chat",
            "ordering": ("-created_at",),
            "constraints": [
                models.UniqueConstraint(fields=("blocker", "blocked"), name="chat_unique_blocker_blocked"),
                models.CheckConstraint(condition=models.Q(("blocker", models.F("blocked")), _negated=True), name="chat_cannot_block_self"),
            ],
        },
    )]
