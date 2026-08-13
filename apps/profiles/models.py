from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models


def profile_photo_path(instance, filename):
    extension = Path(filename).suffix.lower() or ".jpg"
    return f"profiles/{instance.user_id}/{uuid4().hex}{extension}"


phone_validator = RegexValidator(
    regex=r"^[0-9()+\-\s]{8,20}$",
    message="Informe um telefone válido, usando apenas números, espaços, parênteses, + ou -.",
)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="usuário",
    )
    phone = models.CharField(
        "telefone",
        max_length=20,
        blank=True,
        validators=[phone_validator],
    )
    city = models.CharField("cidade", max_length=100, default="Avaré")
    neighborhood = models.CharField("bairro", max_length=100, blank=True)
    bio = models.CharField(
        "breve apresentação",
        max_length=300,
        blank=True,
        help_text="Conte algo breve sobre você. Não inclua informações médicas.",
    )
    photo = models.ImageField(
        "foto de perfil",
        upload_to=profile_photo_path,
        blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "perfil pessoal"
        verbose_name_plural = "perfis pessoais"

    def __str__(self):
        return f"Perfil de {self.user}"
