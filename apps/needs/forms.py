from typing import ClassVar

from django import forms

from apps.professionals.models import ServiceMode

from .models import (
    HelpRequest,
    Need,
    NeedCategory,
    ProfessionalInterest,
    RequestPriority,
)


class QuickHelpRequestForm(forms.Form):
    title = forms.CharField(
        label="Com o que você precisa de ajuda?",
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Ex.: Ajuda para usar o celular"}),
    )
    category = forms.ChoiceField(
        label="Que tipo de ajuda é essa?",
        choices=NeedCategory.choices,
    )
    details = forms.CharField(
        label="Conte um pouco mais",
        max_length=800,
        help_text="Não escreva senhas, documentos ou informações médicas desnecessárias.",
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Explique de forma simples."}),
    )
    region = forms.CharField(
        label="Onde você precisa da ajuda?",
        max_length=150,
        initial="Avaré-SP",
        help_text="Informe somente a cidade ou a região.",
    )
    priority = forms.ChoiceField(
        label="Quando você precisa?",
        choices=RequestPriority.choices,
        initial=RequestPriority.ROUTINE,
    )
    preferred_service_mode = forms.ChoiceField(
        label="Como prefere receber a ajuda?",
        choices=ServiceMode.choices,
        initial=ServiceMode.BOTH,
    )


class NeedForm(forms.ModelForm):
    class Meta:
        model = Need
        fields = ("title", "category", "description")
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "title": forms.TextInput(attrs={"placeholder": "Ex.: Ajuda com celular"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class HelpRequestForm(forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = (
            "need",
            "details",
            "region",
            "priority",
            "preferred_service_mode",
        )
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "details": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, senior, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["need"].queryset = Need.objects.filter(
            senior=senior,
            status="active",
        )
        self.fields["need"].label = "Com o que você precisa de ajuda?"
        self.fields["need"].help_text = "Escolha uma ajuda que você já cadastrou."
        self.fields["details"].label = "Conte um pouco sobre a ajuda"
        self.fields["details"].help_text = (
            "Escreva somente o necessário. Não informe senhas, documentos ou dados médicos."
        )
        self.fields["region"].label = "Onde você precisa da ajuda?"
        self.fields["region"].help_text = "Informe somente a cidade ou a região."
        self.fields["priority"].label = "Quando você precisa?"
        self.fields["preferred_service_mode"].label = "Como prefere receber a ajuda?"


class ProfessionalInterestForm(forms.ModelForm):
    class Meta:
        model = ProfessionalInterest
        fields = ("message",)
        labels: ClassVar[dict[str, str]] = {"message": "Mensagem para a pessoa idosa"}
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Explique brevemente como você pode ajudar.",
                }
            )
        }
