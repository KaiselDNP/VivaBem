from typing import ClassVar

from django import forms

from apps.accounts.models import User, UserRole
from apps.professionals.models import ProfessionalProfile, VerificationStatus

from .models import AdminAnnouncement, AnnouncementAudience, Report, ReportStatus


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("category", "subject", "description")
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "subject": forms.TextInput(attrs={"placeholder": "Resuma o que precisa ser analisado"}),
            "description": forms.Textarea(
                attrs={
                    "rows": 7,
                    "placeholder": "Explique o ocorrido sem incluir senhas ou documentos.",
                }
            ),
        }


class ReportReviewForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("status", "resolution_notes")
        labels: ClassVar[dict[str, str]] = {
            "resolution_notes": "Retorno para quem enviou a denúncia"
        }
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "resolution_notes": forms.Textarea(attrs={"rows": 6}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("status") in {ReportStatus.RESOLVED, ReportStatus.DISMISSED}:
            if not cleaned_data.get("resolution_notes", "").strip():
                self.add_error(
                    "resolution_notes",
                    "Informe um retorno antes de finalizar a denúncia.",
                )
        return cleaned_data


class ProfessionalReviewForm(forms.ModelForm):
    class Meta:
        model = ProfessionalProfile
        fields = ("verification_status", "verification_notes")
        labels: ClassVar[dict[str, str]] = {"verification_notes": "Observações administrativas"}
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "verification_notes": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_verification_status(self):
        status = self.cleaned_data["verification_status"]
        if status == VerificationStatus.VERIFIED and not self.instance.is_complete:
            raise forms.ValidationError(
                "O perfil precisa ter profissão, especialidade e região antes da verificação."
            )
        return status


class AdminAnnouncementForm(forms.ModelForm):
    class Meta:
        model = AdminAnnouncement
        fields = ("audience", "recipient", "title", "message")
        labels: ClassVar[dict[str, str]] = {
            "recipient": "Conta que receberá o aviso",
        }
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "title": forms.TextInput(attrs={"placeholder": "Ex.: Atualização importante"}),
            "message": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Escreva uma mensagem clara e objetiva.",
                }
            ),
        }

    def __init__(self, *args, selected_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient"].queryset = User.objects.filter(is_active=True).exclude(
            role=UserRole.ADMIN
        )
        self.fields["recipient"].required = False
        if selected_user and not self.is_bound:
            self.initial["audience"] = AnnouncementAudience.INDIVIDUAL
            self.initial["recipient"] = selected_user

    def clean(self):
        cleaned_data = super().clean()
        audience = cleaned_data.get("audience")
        recipient = cleaned_data.get("recipient")
        if audience == AnnouncementAudience.INDIVIDUAL and not recipient:
            self.add_error("recipient", "Escolha a conta que receberá o aviso.")
        if audience != AnnouncementAudience.INDIVIDUAL:
            cleaned_data["recipient"] = None
        return cleaned_data
