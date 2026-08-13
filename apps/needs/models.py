from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.professionals.models import ServiceMode


class NeedCategory(models.TextChoices):
    COMPANIONSHIP = "companionship", "Companhia e convivência"
    DAILY_TASKS = "daily_tasks", "Atividades do dia a dia"
    TRANSPORT = "transport", "Transporte e deslocamento"
    DIGITAL = "digital", "Apoio com tecnologia"
    WELLBEING = "wellbeing", "Bem-estar e qualidade de vida"
    OTHER = "other", "Outra necessidade"


class NeedStatus(models.TextChoices):
    ACTIVE = "active", "Ativa"
    RESOLVED = "resolved", "Resolvida"
    ARCHIVED = "archived", "Arquivada"


class Need(models.Model):
    senior = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="needs",
        verbose_name="pessoa idosa",
    )
    title = models.CharField("título", max_length=100)
    category = models.CharField("categoria", max_length=30, choices=NeedCategory.choices)
    description = models.TextField("descrição", max_length=800)
    status = models.CharField(
        "status",
        max_length=15,
        choices=NeedStatus.choices,
        default=NeedStatus.ACTIVE,
    )
    created_at = models.DateTimeField("criada em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        verbose_name = "necessidade"
        verbose_name_plural = "necessidades"
        ordering = ("-created_at",)

    def clean(self):
        super().clean()
        if self.senior_id and self.senior.role != "senior":
            raise ValidationError("Somente uma pessoa idosa pode registrar necessidades.")

    def __str__(self):
        return self.title


class RequestPriority(models.TextChoices):
    ROUTINE = "routine", "Sem pressa"
    SOON = "soon", "Preciso em breve"


class HelpRequestStatus(models.TextChoices):
    OPEN = "open", "Aberta"
    ACCEPTED = "accepted", "Profissional aceito"
    COMPLETED = "completed", "Concluída"
    CANCELED = "canceled", "Cancelada"


class HelpRequest(models.Model):
    need = models.ForeignKey(
        Need,
        on_delete=models.PROTECT,
        related_name="help_requests",
        verbose_name="necessidade",
    )
    details = models.TextField(
        "detalhes do pedido",
        max_length=800,
        help_text="Não informe documentos, senhas ou dados médicos desnecessários.",
    )
    region = models.CharField("região do atendimento", max_length=150, default="Avaré-SP")
    priority = models.CharField(
        "prazo",
        max_length=15,
        choices=RequestPriority.choices,
        default=RequestPriority.ROUTINE,
    )
    preferred_service_mode = models.CharField(
        "modalidade preferida",
        max_length=20,
        choices=ServiceMode.choices,
        default=ServiceMode.BOTH,
    )
    status = models.CharField(
        "status",
        max_length=15,
        choices=HelpRequestStatus.choices,
        default=HelpRequestStatus.OPEN,
    )
    created_at = models.DateTimeField("criada em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        verbose_name = "solicitação de ajuda"
        verbose_name_plural = "solicitações de ajuda"
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [models.Index(fields=("status", "-created_at"))]

    @property
    def senior(self):
        return self.need.senior

    def __str__(self):
        return f"{self.need.title} — {self.get_status_display()}"


class InterestStatus(models.TextChoices):
    PENDING = "pending", "Aguardando resposta"
    ACCEPTED = "accepted", "Aceito"
    REJECTED = "rejected", "Recusado"
    WITHDRAWN = "withdrawn", "Retirado"


class ProfessionalInterest(models.Model):
    help_request = models.ForeignKey(
        HelpRequest,
        on_delete=models.CASCADE,
        related_name="professional_interests",
        verbose_name="solicitação",
    )
    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="professional_interests",
        verbose_name="profissional",
    )
    message = models.CharField("mensagem", max_length=500)
    status = models.CharField(
        "status",
        max_length=15,
        choices=InterestStatus.choices,
        default=InterestStatus.PENDING,
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    responded_at = models.DateTimeField("respondido em", null=True, blank=True)

    class Meta:
        verbose_name = "interesse profissional"
        verbose_name_plural = "interesses profissionais"
        ordering = ("-created_at",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=("help_request", "professional"),
                name="needs_unique_request_professional_interest",
            ),
            models.UniqueConstraint(
                fields=("help_request",),
                condition=Q(status="accepted"),
                name="needs_one_accepted_interest_per_request",
            ),
        ]

    def clean(self):
        super().clean()
        if self.professional_id and self.professional.role != "professional":
            raise ValidationError("Somente profissionais podem demonstrar interesse.")

    def __str__(self):
        return f"{self.professional} → {self.help_request}"
