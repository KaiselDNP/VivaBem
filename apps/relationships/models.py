from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FamilyLinkStatus(models.TextChoices):
    PENDING = "pending", "Aguardando autorização"
    APPROVED = "approved", "Autorizado"
    REJECTED = "rejected", "Recusado"
    REVOKED = "revoked", "Revogado"


class FamilyLink(models.Model):
    senior = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="family_links_as_senior",
        verbose_name="pessoa idosa",
    )
    family = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="family_links_as_family",
        verbose_name="familiar",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="family_links_requested",
        verbose_name="solicitado por",
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=FamilyLinkStatus.choices,
        default=FamilyLinkStatus.PENDING,
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    responded_at = models.DateTimeField("respondido em", null=True, blank=True)

    class Meta:
        verbose_name = "vínculo familiar"
        verbose_name_plural = "vínculos familiares"
        ordering = ("-created_at",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=("senior", "family"),
                name="relationships_unique_senior_family",
            )
        ]

    def clean(self):
        super().clean()
        if self.senior_id and self.senior.role != "senior":
            raise ValidationError("O vínculo exige uma conta de pessoa idosa.")
        if self.family_id and self.family.role != "family":
            raise ValidationError("O vínculo exige uma conta de familiar.")
        if self.requested_by_id and self.requested_by_id not in {self.senior_id, self.family_id}:
            raise ValidationError("A solicitação deve partir de uma das pessoas do vínculo.")

    def __str__(self):
        return f"{self.family} ↔ {self.senior}"


class FamilyPermission(models.Model):
    link = models.OneToOneField(
        FamilyLink,
        on_delete=models.CASCADE,
        related_name="permissions",
        verbose_name="vínculo",
    )
    can_view_needs = models.BooleanField("visualizar necessidades", default=False)
    can_view_requests = models.BooleanField("visualizar solicitações", default=False)
    can_view_professional_interests = models.BooleanField(
        "visualizar interesses profissionais",
        default=False,
    )
    can_receive_notifications = models.BooleanField(
        "receber notificações de acompanhamento",
        default=False,
    )
    can_create_requests = models.BooleanField(
        "criar pedidos de ajuda em meu nome",
        default=False,
    )
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "permissão familiar"
        verbose_name_plural = "permissões familiares"

    def __str__(self):
        return f"Permissões de {self.link}"
