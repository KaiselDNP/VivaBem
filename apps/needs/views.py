from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import UserRole
from apps.notifications.models import NotificationKind
from apps.notifications.services import notify
from apps.professionals.models import ProfessionalProfile

from .forms import HelpRequestForm, NeedForm, ProfessionalInterestForm
from .models import (
    HelpRequest,
    HelpRequestStatus,
    InterestStatus,
    Need,
    NeedStatus,
    ProfessionalInterest,
)
from .services import notify_family_about_request


def require_role(request, role, message):
    if request.user.role != role:
        return HttpResponseForbidden(message)
    return None


@login_required
def need_list(request):
    denied = require_role(request, UserRole.SENIOR, "Somente pessoas idosas acessam necessidades.")
    if denied:
        return denied
    return render(request, "needs/list.html", {"needs": request.user.needs.all()})


@login_required
def need_create(request):
    denied = require_role(request, UserRole.SENIOR, "Somente pessoas idosas criam necessidades.")
    if denied:
        return denied
    form = NeedForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        need = form.save(commit=False)
        need.senior = request.user
        need.save()
        messages.success(request, "Necessidade registrada.")
        return redirect("needs:list")
    return render(request, "needs/form.html", {"form": form, "page_title": "Nova necessidade"})


@login_required
def need_edit(request, pk):
    denied = require_role(request, UserRole.SENIOR, "Somente pessoas idosas editam necessidades.")
    if denied:
        return denied
    need = get_object_or_404(Need, pk=pk, senior=request.user)
    form = NeedForm(request.POST or None, instance=need)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Necessidade atualizada.")
        return redirect("needs:list")
    return render(request, "needs/form.html", {"form": form, "page_title": "Editar necessidade"})


@login_required
@require_POST
def need_resolve(request, pk):
    denied = require_role(request, UserRole.SENIOR, "Somente a pessoa idosa altera a necessidade.")
    if denied:
        return denied
    need = get_object_or_404(Need, pk=pk, senior=request.user)
    need.status = NeedStatus.RESOLVED
    need.save(update_fields=("status", "updated_at"))
    return redirect("needs:list")


@login_required
def request_list(request):
    denied = require_role(request, UserRole.SENIOR, "Somente pessoas idosas acessam seus pedidos.")
    if denied:
        return denied
    requests = HelpRequest.objects.filter(need__senior=request.user).select_related("need")
    return render(request, "needs/request_list.html", {"help_requests": requests})


@login_required
def request_create(request):
    denied = require_role(request, UserRole.SENIOR, "Somente pessoas idosas solicitam ajuda.")
    if denied:
        return denied
    form = HelpRequestForm(request.POST or None, senior=request.user)
    if request.method == "POST" and form.is_valid():
        help_request = form.save()
        notify_family_about_request(
            help_request,
            "Nova solicitação de ajuda",
            f"{request.user} criou uma solicitação que você pode acompanhar.",
        )
        messages.success(request, "Solicitação de ajuda publicada.")
        return redirect("needs:request_detail", pk=help_request.pk)
    return render(request, "needs/request_form.html", {"form": form})


@login_required
def request_detail(request, pk):
    denied = require_role(request, UserRole.SENIOR, "Somente a pessoa idosa acessa este pedido.")
    if denied:
        return denied
    help_request = get_object_or_404(
        HelpRequest.objects.select_related("need"), pk=pk, need__senior=request.user
    )
    interests = help_request.professional_interests.select_related(
        "professional", "professional__professional_profile"
    )
    return render(
        request,
        "needs/request_detail.html",
        {"help_request": help_request, "interests": interests},
    )


@login_required
@require_POST
def request_status(request, pk, action):
    denied = require_role(request, UserRole.SENIOR, "Somente a pessoa idosa altera este pedido.")
    if denied:
        return denied
    help_request = get_object_or_404(
        HelpRequest.objects.select_related("need"),
        pk=pk,
        need__senior=request.user,
    )
    transitions = {
        "cancel": (
            {HelpRequestStatus.OPEN, HelpRequestStatus.ACCEPTED},
            HelpRequestStatus.CANCELED,
        ),
        "complete": ({HelpRequestStatus.ACCEPTED}, HelpRequestStatus.COMPLETED),
    }
    if action not in transitions or help_request.status not in transitions[action][0]:
        return HttpResponseForbidden("Esta alteração de status não é permitida.")
    help_request.status = transitions[action][1]
    help_request.save(update_fields=("status", "updated_at"))
    accepted_interest = (
        help_request.professional_interests.filter(status=InterestStatus.ACCEPTED)
        .select_related("professional")
        .first()
    )
    if accepted_interest:
        notify(
            recipient=accepted_interest.professional,
            kind=NotificationKind.INTEREST_RESPONSE,
            title="Solicitação atualizada",
            message=f"A solicitação agora está como {help_request.get_status_display().lower()}.",
            target_url=reverse("needs:opportunities"),
        )
    notify_family_about_request(
        help_request,
        "Solicitação atualizada",
        f"Uma solicitação acompanhada agora está como {help_request.get_status_display().lower()}.",
    )
    messages.success(request, "Status da solicitação atualizado.")
    return redirect("needs:request_detail", pk=help_request.pk)


@login_required
def opportunities(request):
    denied = require_role(
        request,
        UserRole.PROFESSIONAL,
        "Somente profissionais acessam oportunidades.",
    )
    if denied:
        return denied
    professional_profile, _ = ProfessionalProfile.objects.get_or_create(user=request.user)
    query = request.GET.get("q", "").strip()
    opportunities_qs = HelpRequest.objects.filter(status=HelpRequestStatus.OPEN).select_related(
        "need"
    )
    if professional_profile.service_mode != "both":
        opportunities_qs = opportunities_qs.filter(
            Q(preferred_service_mode=professional_profile.service_mode)
            | Q(preferred_service_mode="both")
        )
    if query:
        opportunities_qs = opportunities_qs.filter(
            Q(need__title__icontains=query)
            | Q(need__description__icontains=query)
            | Q(region__icontains=query)
        )
    existing_interest_ids = set(
        request.user.professional_interests.values_list("help_request_id", flat=True)
    )
    return render(
        request,
        "needs/opportunities.html",
        {
            "opportunities": opportunities_qs[:50],
            "query": query,
            "professional_profile": professional_profile,
            "existing_interest_ids": existing_interest_ids,
        },
    )


@login_required
def express_interest(request, pk):
    denied = require_role(
        request, UserRole.PROFESSIONAL, "Somente profissionais podem se interessar."
    )
    if denied:
        return denied
    help_request = get_object_or_404(
        HelpRequest.objects.select_related("need", "need__senior"),
        pk=pk,
        status=HelpRequestStatus.OPEN,
    )
    professional_profile, _ = ProfessionalProfile.objects.get_or_create(user=request.user)
    if not professional_profile.is_complete:
        messages.error(request, "Complete seu perfil profissional antes de enviar interesses.")
        return redirect("accounts:profile_edit")
    if ProfessionalInterest.objects.filter(
        help_request=help_request, professional=request.user
    ).exists():
        messages.info(request, "Você já demonstrou interesse nesta solicitação.")
        return redirect("needs:opportunities")
    form = ProfessionalInterestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        interest = form.save(commit=False)
        interest.help_request = help_request
        interest.professional = request.user
        interest.save()
        notify(
            recipient=help_request.senior,
            kind=NotificationKind.PROFESSIONAL_INTEREST,
            title="Profissional interessado",
            message=f"{request.user} demonstrou interesse em {help_request.need.title}.",
            target_url=reverse("needs:request_detail", args=(help_request.pk,)),
        )
        notify_family_about_request(
            help_request,
            "Novo interesse profissional",
            "Uma solicitação acompanhada recebeu interesse de um profissional.",
            interests=True,
        )
        messages.success(request, "Interesse enviado para avaliação da pessoa idosa.")
        return redirect("needs:opportunities")
    return render(
        request,
        "needs/interest_form.html",
        {"form": form, "help_request": help_request},
    )


@login_required
@require_POST
@transaction.atomic
def respond_interest(request, request_pk, interest_pk, action):
    denied = require_role(request, UserRole.SENIOR, "Somente a pessoa idosa responde ao interesse.")
    if denied:
        return denied
    help_request = get_object_or_404(
        HelpRequest.objects.select_for_update().select_related("need"),
        pk=request_pk,
        need__senior=request.user,
        status=HelpRequestStatus.OPEN,
    )
    interest = get_object_or_404(
        ProfessionalInterest.objects.select_related("professional"),
        pk=interest_pk,
        help_request=help_request,
        status=InterestStatus.PENDING,
    )
    if action not in {"accept", "reject"}:
        return HttpResponseForbidden("Ação inválida.")
    interest.status = InterestStatus.ACCEPTED if action == "accept" else InterestStatus.REJECTED
    interest.responded_at = timezone.now()
    interest.save(update_fields=("status", "responded_at"))
    if action == "accept":
        help_request.status = HelpRequestStatus.ACCEPTED
        help_request.save(update_fields=("status", "updated_at"))
        other_interests = list(
            help_request.professional_interests.filter(status=InterestStatus.PENDING)
            .exclude(pk=interest.pk)
            .select_related("professional")
        )
        for other_interest in other_interests:
            other_interest.status = InterestStatus.REJECTED
            other_interest.responded_at = timezone.now()
            other_interest.save(update_fields=("status", "responded_at"))
            notify(
                recipient=other_interest.professional,
                kind=NotificationKind.INTEREST_RESPONSE,
                title="Solicitação preenchida",
                message="A pessoa idosa selecionou outro profissional para esta solicitação.",
                target_url=reverse("needs:opportunities"),
            )
        notify_family_about_request(
            help_request,
            "Profissional aceito",
            "A pessoa idosa aceitou um profissional em uma solicitação acompanhada.",
            interests=True,
        )
    notify(
        recipient=interest.professional,
        kind=NotificationKind.INTEREST_RESPONSE,
        title="Resposta ao seu interesse",
        message=f"Seu interesse foi {interest.get_status_display().lower()}.",
        target_url=reverse("needs:opportunities"),
    )
    messages.success(request, "Resposta enviada ao profissional.")
    return redirect("needs:request_detail", pk=help_request.pk)
