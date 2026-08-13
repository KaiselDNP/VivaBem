from typing import ClassVar

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.accounts.models import User

from .models import UserProfile


class AccountDetailsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")
        labels: ClassVar[dict[str, str]] = {"first_name": "Nome", "last_name": "Sobrenome"}
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
        }


class ProfileForm(forms.ModelForm):
    remove_photo = forms.BooleanField(
        label="Remover foto atual",
        required=False,
    )

    class Meta:
        model = UserProfile
        fields = ("phone", "city", "neighborhood", "bio", "photo")
        labels: ClassVar[dict[str, str]] = {
            "phone": "Telefone (opcional)",
            "city": "Cidade",
            "neighborhood": "Bairro (opcional)",
            "bio": "Sobre você (opcional)",
            "photo": "Escolher uma foto",
        }
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "phone": forms.TextInput(
                attrs={"autocomplete": "tel", "placeholder": "(14) 99999-9999"}
            ),
            "city": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "neighborhood": forms.TextInput(attrs={"autocomplete": "address-level3"}),
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": 300,
                    "placeholder": "Conte algo breve sobre você.",
                }
            ),
            "photo": forms.ClearableFileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp",
                    "data-photo-input": True,
                }
            ),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo:
            return photo

        if not isinstance(photo, UploadedFile):
            return photo

        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("A foto deve ter no máximo 5 MB.")

        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if getattr(photo, "content_type", None) not in allowed_types:
            raise forms.ValidationError("Envie uma imagem JPG, PNG ou WebP.")
        return photo

    @transaction.atomic
    def save(self, commit=True):
        profile = super().save(commit=False)
        old_photo_name = None
        if profile.pk:
            old_photo_name = (
                UserProfile.objects.filter(pk=profile.pk).values_list("photo", flat=True).first()
            )

        if self.cleaned_data.get("remove_photo"):
            profile.photo = None

        if commit:
            profile.save()
            new_photo_name = profile.photo.name if profile.photo else None
            if old_photo_name and old_photo_name != new_photo_name:
                storage = self._meta.model._meta.get_field("photo").storage
                transaction.on_commit(lambda: storage.delete(old_photo_name))
        return profile
