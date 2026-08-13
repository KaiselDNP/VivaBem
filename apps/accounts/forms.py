from typing import ClassVar

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone

from .models import User, UserRole


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "autofocus": True,
                "placeholder": "voce@exemplo.com",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "placeholder": "Digite sua senha"}
        ),
    )
    error_messages: ClassVar[dict[str, str]] = {
        "invalid_login": "E-mail ou senha inválidos. Confira os dados e tente novamente.",
        "inactive": "Esta conta está inativa.",
    }

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "voce@exemplo.com"}),
    )
    accepted_privacy = forms.BooleanField(
        label="Li e aceito o aviso de privacidade do VivaBem.",
        error_messages={"required": "Você precisa aceitar o aviso de privacidade."},
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, role, **kwargs):
        super().__init__(*args, **kwargs)
        if role not in {UserRole.SENIOR, UserRole.FAMILY, UserRole.PROFESSIONAL}:
            raise ValueError("Perfil de cadastro não permitido.")
        self.role = role
        self.fields["password1"].label = "Senha"
        self.fields["password1"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Crie uma senha segura"}
        )
        self.fields["password2"].label = "Confirme a senha"
        self.fields["password2"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Repita a senha"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.role
        user.accepted_terms_at = timezone.now()
        if commit:
            user.save()
            from apps.profiles.models import UserProfile

            UserProfile.objects.get_or_create(user=user)
            if user.role == UserRole.PROFESSIONAL:
                from apps.professionals.models import ProfessionalProfile

                ProfessionalProfile.objects.get_or_create(user=user)
        return user
