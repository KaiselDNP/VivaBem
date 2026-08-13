from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class ServiceMode(models.TextChoices):
    VOLUNTEER = "volunteer", "Somente voluntário"
    PAID = "paid", "Somente remunerado"
    BOTH = "both", "Voluntário e remunerado"


class VerificationStatus(models.TextChoices):
    PENDING = "pending", "Aguardando análise"
    VERIFIED = "verified", "Cadastro verificado"
    NEEDS_REVIEW = "needs_review", "Revisão necessária"


class ProfessionalProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="professional_profile",
        verbose_name="usuário",
    )
    profession = models.CharField("profissão", max_length=100)
    specialty = models.CharField("especialidade", max_length=150)
    council = models.CharField(
        "conselho ou órgão profissional",
        max_length=50,
        blank=True,
        help_text="Exemplo: CREFITO, COREN ou outro órgão aplicável.",
    )
    registration_number = models.CharField(
        "número de registro",
        max_length=50,
        blank=True,
    )
    service_region = models.CharField(
        "região de atendimento",
        max_length=150,
        default="Avaré-SP",
    )
    service_mode = models.CharField(
        "modalidade de atendimento",
        max_length=20,
        choices=ServiceMode.choices,
        default=ServiceMode.BOTH,
    )
    verification_status = models.CharField(
        "status da verificação",
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verification_notes = models.TextField(
        "observações administrativas",
        blank=True,
        help_text="Visível apenas na administração.",
    )
    verified_at = models.DateTimeField("verificado em", null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="professional_profiles_verified",
        verbose_name="verificado por",
    )
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "perfil profissional"
        verbose_name_plural = "perfis profissionais"
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=("council", "registration_number"),
                condition=~Q(council="") & ~Q(registration_number=""),
                name="professionals_unique_nonempty_credential",
            )
        ]

    @property
    def is_complete(self):
        return bool(self.profession and self.specialty and self.service_region)

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != "professional":
            raise ValidationError("O perfil profissional exige uma conta do tipo profissional.")

    def __str__(self):
        return f"{self.user} — {self.profession or 'perfil incompleto'}"
