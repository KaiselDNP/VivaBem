import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.notifications.models import NotificationKind
from apps.notifications.services import notify

from .models import ChatModerationEvent

CATEGORY_LABELS = {
    "threat": "ameaça",
    "harassment": "assédio ou ofensa",
    "sensitive_data": "solicitação de dado sensível",
    "financial_pressure": "pressão financeira suspeita",
}

BLOCKED_PHRASES = {
    "threat": (
        "vou te matar",
        "vou matar voce",
        "voce vai morrer",
        "vou te bater",
        "vou te machucar",
        "vou acabar com voce",
        "vou te arrebentar",
    ),
    "harassment": (
        "idiota",
        "imbecil",
        "inutil",
        "otario",
        "vagabundo",
        "desgracado",
    ),
    "sensitive_data": (
        "manda sua senha",
        "mande sua senha",
        "me passe sua senha",
        "informe sua senha",
        "envie seu cpf",
        "manda seu cpf",
        "mande seu cpf",
        "me envie seu documento",
    ),
    "financial_pressure": (
        "faca um pix agora",
        "manda um pix agora",
        "mande um pix agora",
        "envie um pix agora",
    ),
}


@dataclass(frozen=True)
class ModerationResult:
    categories: tuple[str, ...]

    @property
    def blocked(self):
        return bool(self.categories)

    @property
    def category_labels(self):
        return tuple(CATEGORY_LABELS[category] for category in self.categories)


def normalize_message(value):
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def moderate_message(value):
    normalized = f" {normalize_message(value)} "
    categories = tuple(
        category
        for category, phrases in BLOCKED_PHRASES.items()
        if any(f" {phrase} " in normalized for phrase in phrases)
    )
    return ModerationResult(categories=categories)


@transaction.atomic
def record_blocked_message(*, conversation, sender, recipient, result, message_length):
    event = ChatModerationEvent.objects.create(
        conversation=conversation,
        sender=sender,
        recipient=recipient,
        matched_categories=",".join(result.categories),
        message_length=message_length,
    )
    labels = ", ".join(result.category_labels)
    user_label = sender.get_full_name() or sender.email
    target_url = f"{reverse('moderation:admin_users')}?{urlencode({'q': sender.email})}"
    administrators = (
        get_user_model()
        .objects.filter(is_active=True)
        .filter(Q(role=UserRole.ADMIN) | Q(is_staff=True) | Q(is_superuser=True))
    )
    for administrator in administrators:
        notify(
            recipient=administrator,
            kind=NotificationKind.CHAT_MODERATION,
            title="Mensagem bloqueada no chat",
            message=f"Tentativa de {user_label} bloqueada. Motivo: {labels}.",
            target_url=target_url,
        )
    return event
