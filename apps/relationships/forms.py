from typing import ClassVar

from django import forms

from apps.accounts.models import User, UserRole

from .models import FamilyPermission


class FamilyLinkRequestForm(forms.Form):
    senior_email = forms.EmailField(
        label="E-mail da pessoa idosa",
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "placeholder": "idoso@exemplo.com"}
        ),
    )

    def clean_senior_email(self):
        return self.cleaned_data["senior_email"].strip().lower()

    def get_senior(self):
        return User.objects.filter(
            email__iexact=self.cleaned_data["senior_email"],
            role=UserRole.SENIOR,
            is_active=True,
        ).first()


class FamilyPermissionForm(forms.ModelForm):
    class Meta:
        model = FamilyPermission
        fields = (
            "can_view_needs",
            "can_view_requests",
            "can_view_professional_interests",
            "can_receive_notifications",
            "can_create_requests",
        )
        labels: ClassVar[dict[str, str]] = {
            "can_view_needs": "Pode ver as ajudas que cadastrei",
            "can_view_requests": "Pode acompanhar meus pedidos de ajuda",
            "can_view_professional_interests": "Pode ver profissionais que se ofereceram",
            "can_receive_notifications": "Pode receber avisos sobre meu acompanhamento",
            "can_create_requests": "Pode criar pedidos de ajuda em meu nome",
        }
        help_texts: ClassVar[dict[str, str]] = {
            "can_view_needs": "Mostra os assuntos para os quais você procura apoio.",
            "can_view_requests": "Mostra o andamento e as informações dos seus pedidos.",
            "can_view_professional_interests": (
                "Mostra nomes e mensagens dos profissionais interessados."
            ),
            "can_receive_notifications": "Envia ao familiar avisos sobre mudanças importantes.",
            "can_create_requests": (
                "Permite preparar e publicar um pedido. "
                "A escolha do profissional continua sendo sua."
            ),
        }
