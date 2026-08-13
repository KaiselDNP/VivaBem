from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from .managers import UserManager


class UserRole(models.TextChoices):
    SENIOR = "senior", "Pessoa idosa"
    FAMILY = "family", "Familiar"
    PROFESSIONAL = "professional", "Profissional"
    ADMIN = "admin", "Administrador"


class User(AbstractUser):
    """Identidade central do sistema, autenticada por e-mail."""

    username = None
    email = models.EmailField("e-mail", unique=True)
    role = models.CharField("perfil de acesso", max_length=20, choices=UserRole.choices)
    accepted_terms_at = models.DateTimeField(
        "termos aceitos em",
        null=True,
        blank=True,
        help_text="Registra quando o usuário aceitou os termos e o aviso de privacidade.",
    )

    USERNAME_FIELD: ClassVar[str] = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects = UserManager()

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ("first_name", "last_name", "email")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()

    def __str__(self):
        return self.get_full_name() or self.email
