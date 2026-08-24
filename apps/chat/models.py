from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Conversation(models.Model):
    participant_one = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations_as_first",
        verbose_name="primeiro participante",
    )
    participant_two = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations_as_second",
        verbose_name="segundo participante",
    )
    created_at = models.DateTimeField("criada em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        verbose_name = "conversa"
        verbose_name_plural = "conversas"
        ordering = ("-updated_at",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=("participant_one", "participant_two"),
                name="chat_unique_participant_pair",
            ),
            models.CheckConstraint(
                condition=Q(participant_one_id__lt=F("participant_two_id")),
                name="chat_participants_canonical_order",
            ),
        ]

    def clean(self):
        super().clean()
        if self.participant_one_id and self.participant_two_id:
            if self.participant_one_id >= self.participant_two_id:
                raise ValidationError(
                    "Os participantes precisam estar em ordem válida e ser distintos."
                )

    def other_participant(self, user):
        if user.pk == self.participant_one_id:
            return self.participant_two
        if user.pk == self.participant_two_id:
            return self.participant_one
        raise ValueError("O usuário não participa desta conversa.")

    def __str__(self):
        return f"{self.participant_one} ↔ {self.participant_two}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="conversa",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages_sent",
        verbose_name="remetente",
    )
    body = models.TextField("mensagem", max_length=1000)
    read_at = models.DateTimeField("lida em", null=True, blank=True)
    created_at = models.DateTimeField("enviada em", auto_now_add=True)

    class Meta:
        verbose_name = "mensagem"
        verbose_name_plural = "mensagens"
        ordering = ("created_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=("conversation", "created_at")),
            models.Index(fields=("conversation", "read_at")),
        ]

    def clean(self):
        super().clean()
        if self.conversation_id and self.sender_id not in {
            self.conversation.participant_one_id,
            self.conversation.participant_two_id,
        }:
            raise ValidationError("O remetente precisa participar da conversa.")

    def __str__(self):
        return f"{self.sender}: {self.body[:50]}"


class ChatModerationEvent(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="moderation_events",
        verbose_name="conversa",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="chat_moderation_events_sent",
        verbose_name="remetente",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="chat_moderation_events_received",
        verbose_name="destinatário",
    )
    matched_categories = models.CharField("categorias detectadas", max_length=120)
    message_length = models.PositiveIntegerField("tamanho da mensagem")
    created_at = models.DateTimeField("registrado em", auto_now_add=True)

    class Meta:
        verbose_name = "evento de moderação do chat"
        verbose_name_plural = "eventos de moderação do chat"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Evento {self.pk} — {self.matched_categories}"


class ChatBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_blocks_created",
        verbose_name="quem bloqueou",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_blocks_received",
        verbose_name="conta bloqueada",
    )
    created_at = models.DateTimeField("bloqueado em", auto_now_add=True)

    class Meta:
        verbose_name = "bloqueio de chat"
        verbose_name_plural = "bloqueios de chat"
        ordering = ("-created_at",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=("blocker", "blocked"),
                name="chat_unique_blocker_blocked",
            ),
            models.CheckConstraint(
                condition=~Q(blocker=F("blocked")),
                name="chat_cannot_block_self",
            ),
        ]

    def clean(self):
        super().clean()
        if self.blocker_id and self.blocker_id == self.blocked_id:
            raise ValidationError("Não é possível bloquear a própria conta.")

    def __str__(self):
        return f"{self.blocker} bloqueou {self.blocked}"
