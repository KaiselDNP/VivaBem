from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import EmailAuthenticationForm, SignUpForm
from .models import UserRole


class AnonymousOnlyMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:dashboard")
        return super().dispatch(request, *args, **kwargs)


class VivaBemLoginView(AnonymousOnlyMixin, LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class SignUpChoiceView(AnonymousOnlyMixin, TemplateView):
    template_name = "accounts/signup_choice.html"


class SignUpView(AnonymousOnlyMixin, FormView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:dashboard")
    role = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["role"] = self.role
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_label"] = UserRole(self.role).label
        context["role_slug"] = self.role
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Conta criada com segurança. Boas-vindas ao VivaBem!")
        return super().form_valid(form)


class SeniorSignUpView(SignUpView):
    role = UserRole.SENIOR


class FamilySignUpView(SignUpView):
    role = UserRole.FAMILY


class ProfessionalSignUpView(SignUpView):
    role = UserRole.PROFESSIONAL

    def get_success_url(self):
        return reverse_lazy("accounts:profile_edit")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        from apps.professionals.models import ProfessionalProfile
        from apps.profiles.models import UserProfile

        context = super().get_context_data(**kwargs)
        context["profile"], _ = UserProfile.objects.get_or_create(user=self.request.user)
        if self.request.user.role == UserRole.PROFESSIONAL:
            context["professional_profile"], _ = ProfessionalProfile.objects.get_or_create(
                user=self.request.user
            )
        return context
