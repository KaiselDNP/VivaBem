from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ReportCategory(models.TextChoices):
    INAPPROPRIATE_BEHAVIOR = "behavior", "Comportamento inadequado"
    FALSE_INFORMATION = "false_information", "Informação possivelmente falsa"
    PRIVACY = "privacy", "Privacidade ou uso indevido de dados"
    PROFESSIONAL_PROFILE = "professional_profile", "Perfil profissional"
    TECHNICAL = "technical", "Problema técnico"
    OTHER = "other", "Outro assunto"


class ReportStatus(models.TextChoices):
    OPEN = "open", "Recebida"
    IN_REVIEW = "in_review", "Em análise"
    RESOLVED = "resolved", "Resolvida"
    DISMISSED = "dismissed", "Encerrada sem ação"


class Report(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports_created",
        verbose_name="autor da denúncia",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_received",
        verbose_name="usuário denunciado",
    )
    category = models.CharField("categoria", max_length=30, choices=ReportCategory.choices)
    subject = models.CharField("assunto", max_length=120)
    description = models.TextField("descrição", max_length=1500)
    status = models.CharField(
        "status",
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.OPEN,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_assigned",
        verbose_name="responsável pela análise",
    )
    resolution_notes = models.TextField("retorno da administração", max_length=1000, blank=True)
    created_at = models.DateTimeField("criada em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizada em", auto_now=True)
    resolved_at = models.DateTimeField("finalizada em", null=True, blank=True)

    class Meta:
        verbose_name = "denúncia"
        verbose_name_plural = "denúncias"
        ordering = ("-created_at",)

    def clean(self):
        super().clean()
        if self.reporter_id and self.reported_user_id == self.reporter_id:
            raise ValidationError("Não é possível denunciar a própria conta.")

    def __str__(self):
        return f"#{self.pk or 'nova'} — {self.subject}"


class AuditAction(models.TextChoices):
    REPORT_REVIEW = "report_review", "Análise de denúncia"
    PROFESSIONAL_REVIEW = "professional_review", "Análise de profissional"
    USER_STATUS = "user_status", "Alteração de conta"
    NOTICE_SENT = "notice_sent", "Envio de aviso"


class AnnouncementAudience(models.TextChoices):
    INDIVIDUAL = "individual", "Uma conta específica"
    SENIORS = "senior", "Todas as pessoas idosas"
    FAMILIES = "family", "Todos os familiares"
    PROFESSIONALS = "professional", "Todos os profissionais"
    ALL_USERS = "all", "Todos os usuários não administrativos"


class AdminAnnouncement(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="announcements_created",
        verbose_name="administrador",
    )
    title = models.CharField("título", max_length=120)
    message = models.TextField("mensagem", max_length=300)
    audience = models.CharField(
        "destinatários",
        max_length=20,
        choices=AnnouncementAudience.choices,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_admin_announcements",
        verbose_name="conta específica",
    )
    recipients_count = models.PositiveIntegerField("quantidade de destinatários", default=0)
    created_at = models.DateTimeField("enviado em", auto_now_add=True)

    class Meta:
        verbose_name = "aviso administrativo"
        verbose_name_plural = "avisos administrativos"
        ordering = ("-created_at",)

    def clean(self):
        super().clean()
        if self.audience == AnnouncementAudience.INDIVIDUAL and not self.recipient_id:
            raise ValidationError("Escolha a conta que receberá o aviso.")
        if self.audience != AnnouncementAudience.INDIVIDUAL and self.recipient_id:
            raise ValidationError("Avisos para grupos não devem possuir uma conta específica.")

    def __str__(self):
        return self.title


class AdminAuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderation_actions",
        verbose_name="administrador",
    )
    action = models.CharField("ação", max_length=30, choices=AuditAction.choices)
    target_type = models.CharField("tipo do registro", max_length=40)
    target_id = models.PositiveBigIntegerField("identificador do registro")
    target_label = models.CharField("identificação resumida", max_length=150)
    description = models.CharField("descrição", max_length=500)
    created_at = models.DateTimeField("realizada em", auto_now_add=True)

    class Meta:
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_action_display()} — {self.target_label}"
