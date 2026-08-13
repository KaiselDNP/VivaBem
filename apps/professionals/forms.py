from typing import ClassVar

from django import forms

from .models import ProfessionalProfile, VerificationStatus


class ProfessionalProfileForm(forms.ModelForm):
    editable_credential_fields: ClassVar[tuple[str, ...]] = (
        "profession",
        "specialty",
        "council",
        "registration_number",
        "service_region",
        "service_mode",
    )

    class Meta:
        model = ProfessionalProfile
        fields = (
            "profession",
            "specialty",
            "council",
            "registration_number",
            "service_region",
            "service_mode",
        )
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "profession": forms.TextInput(attrs={"placeholder": "Ex.: Fisioterapeuta"}),
            "specialty": forms.TextInput(attrs={"placeholder": "Ex.: Gerontologia"}),
            "council": forms.TextInput(attrs={"placeholder": "Ex.: CREFITO"}),
            "registration_number": forms.TextInput(attrs={"placeholder": "Número e região"}),
            "service_region": forms.TextInput(attrs={"placeholder": "Ex.: Avaré-SP e região"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        council = cleaned_data.get("council", "").strip()
        registration = cleaned_data.get("registration_number", "").strip()
        if bool(council) != bool(registration):
            raise forms.ValidationError(
                "Informe o conselho e o número de registro juntos, ou deixe ambos em branco."
            )
        cleaned_data["council"] = council.upper()
        cleaned_data["registration_number"] = registration.upper()
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        credentials_changed = any(
            field in self.changed_data for field in self.editable_credential_fields
        )
        if credentials_changed and profile.verification_status != VerificationStatus.PENDING:
            profile.verification_status = VerificationStatus.PENDING
            profile.verified_at = None
            profile.verified_by = None
        if commit:
            profile.save()
        return profile
