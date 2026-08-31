import mimetypes

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.accounts.models import UserRole
from apps.professionals.forms import ProfessionalProfileForm
from apps.professionals.models import ProfessionalProfile

from .forms import AccountDetailsForm, ProfileForm
from .models import UserProfile


class ProfileEditView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/edit.html"

    def get_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = kwargs.get("profile") or self.get_profile()
        context["profile"] = profile
        context["account_form"] = kwargs.get("account_form") or AccountDetailsForm(
            instance=self.request.user
        )
        context["profile_form"] = kwargs.get("profile_form") or ProfileForm(instance=profile)
        context["professional_form"] = kwargs.get("professional_form")
        context["professional_profile"] = kwargs.get("professional_profile")
        if self.request.user.role == UserRole.PROFESSIONAL:
            professional_profile = context["professional_profile"]
            if professional_profile is None:
                professional_profile, _ = ProfessionalProfile.objects.get_or_create(
                    user=self.request.user
                )
            context["professional_profile"] = professional_profile
            if context["professional_form"] is None:
                context["professional_form"] = ProfessionalProfileForm(
                    instance=professional_profile
                )
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        profile = self.get_profile()
        account_form = AccountDetailsForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        professional_form = None
        professional_profile = None
        if request.user.role == UserRole.PROFESSIONAL:
            professional_profile, _ = ProfessionalProfile.objects.get_or_create(user=request.user)
            professional_form = ProfessionalProfileForm(
                request.POST,
                instance=professional_profile,
            )

        base_forms_are_valid = account_form.is_valid() and profile_form.is_valid()
        professional_form_is_valid = professional_form is None or professional_form.is_valid()
        if base_forms_are_valid:
            account_form.save()
            profile_form.save()
            if professional_form and professional_form_is_valid:
                professional_form.save()
            if professional_form is None or professional_form_is_valid:
                messages.success(request, "Perfil atualizado com segurança.")
                return redirect("accounts:profile_edit")

            messages.success(
                request,
                "Sua foto e seus dados pessoais foram salvos. "
                "Corrija os dados profissionais marcados.",
            )

        context = self.get_context_data(
            account_form=account_form,
            profile_form=profile_form,
            profile=profile,
            professional_form=professional_form,
            professional_profile=professional_profile,
        )
        return self.render_to_response(context)


def profile_photo(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    try:
        photo = request.user.profile.photo
    except UserProfile.DoesNotExist as exc:
        raise Http404 from exc

    if not photo:
        raise Http404

    content_type = mimetypes.guess_type(photo.name)[0] or "application/octet-stream"
    response = FileResponse(photo.open("rb"), content_type=content_type)
    response["Cache-Control"] = "private, no-cache, no-store, max-age=0"
    response["X-Content-Type-Options"] = "nosniff"
    return response
