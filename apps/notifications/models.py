from typing import ClassVar

from django.conf import settings
from django.db import models


class NotificationKind(models.TextChoices):
    FAMILY_LINK = "family_link", "Vínculo familiar"
    HELP_REQUEST = "help_request", "Solicitação de ajuda"
    PROFESSIONAL_INTEREST = "professional_interest", "Interesse profissional"
    INTEREST_RESPONSE = "interest_response", "Resposta ao interesse"
    REPORT_UPDATE = "report_update", "Atualização de denúncia"
    PROFESSIONAL_REVIEW = "professional_review", "Análise do perfil profissional"
    ACCOUNT_STATUS = "account_status", "Situação da conta"
    ADMIN_NOTICE = "admin_notice", "Aviso da administração"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="destinatário",
    )
    kind = models.CharField("tipo", max_length=30, choices=NotificationKind.choices)
    title = models.CharField("título", max_length=120)
    message = models.CharField("mensagem", max_length=300)
    target_url = models.CharField("destino", max_length=250, blank=True)
    read_at = models.DateTimeField("lida em", null=True, blank=True)
    created_at = models.DateTimeField("criada em", auto_now_add=True)

    class Meta:
        verbose_name = "notificação"
        verbose_name_plural = "notificações"
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [models.Index(fields=("recipient", "read_at", "-created_at"))]

    @property
    def is_read(self):
        return self.read_at is not None

    def __str__(self):
        return f"{self.recipient}: {self.title}"
