from typing import ClassVar

from django import forms

from .models import HelpRequest, Need, ProfessionalInterest


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
