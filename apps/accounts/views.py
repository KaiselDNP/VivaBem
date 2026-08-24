from hashlib import sha256

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import (
    EmailAuthenticationForm,
    SignUpForm,
    VivaBemPasswordResetForm,
    VivaBemSetPasswordForm,
)
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

    def get_throttle_key(self):
        email = self.request.POST.get("username", "").strip().lower()
        remote_address = self.request.META.get("REMOTE_ADDR", "unknown")
        digest = sha256(f"{remote_address}|{email}".encode()).hexdigest()
        return f"vivabem:login-attempts:{digest}"

    def post(self, request, *args, **kwargs):
        self.throttle_key = self.get_throttle_key()
        attempts = int(cache.get(self.throttle_key, 0))
        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            form = self.get_form()
            form.add_error(
                None,
                "Muitas tentativas de entrada. Aguarde alguns minutos e tente novamente.",
            )
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        key = getattr(self, "throttle_key", None)
        if key:
            if not cache.add(key, 1, timeout=settings.LOGIN_LOCKOUT_SECONDS):
                cache.incr(key)
        return super().form_invalid(form)

    def form_valid(self, form):
        key = getattr(self, "throttle_key", None)
        if key:
            cache.delete(key)
        return super().form_valid(form)


class VivaBemPasswordResetView(AnonymousOnlyMixin, PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    form_class = VivaBemPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class VivaBemPasswordResetDoneView(AnonymousOnlyMixin, PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class VivaBemPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = VivaBemSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class VivaBemPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


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
        from apps.needs.models import HelpRequest, HelpRequestStatus
        from apps.professionals.models import ProfessionalProfile
        from apps.profiles.models import UserProfile
        from apps.relationships.models import FamilyLink, FamilyLinkStatus

        context = super().get_context_data(**kwargs)
        context["profile"], _ = UserProfile.objects.get_or_create(user=self.request.user)
        if self.request.user.role == UserRole.SENIOR:
            senior_requests = HelpRequest.objects.filter(
                need__senior=self.request.user
            ).select_related("need")
            context["recent_help_requests"] = senior_requests[:1]
            context["active_request_count"] = senior_requests.filter(
                status__in=(HelpRequestStatus.OPEN, HelpRequestStatus.ACCEPTED)
            ).count()
            context["pending_family_count"] = FamilyLink.objects.filter(
                senior=self.request.user,
                status=FamilyLinkStatus.PENDING,
            ).count()
        if self.request.user.role == UserRole.PROFESSIONAL:
            context["professional_profile"], _ = ProfessionalProfile.objects.get_or_create(
                user=self.request.user
            )
        return context
