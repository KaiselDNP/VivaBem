from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import UserRole
from apps.needs.models import HelpRequest, ProfessionalInterest
from apps.notifications.models import NotificationKind
from apps.notifications.services import notify

from .forms import FamilyLinkRequestForm, FamilyPermissionForm
from .models import FamilyLink, FamilyLinkStatus, FamilyPermission


@login_required
def link_list(request):
    if request.user.role == UserRole.SENIOR:
        links = FamilyLink.objects.filter(senior=request.user).select_related(
            "family", "permissions"
        )
    elif request.user.role == UserRole.FAMILY:
        links = FamilyLink.objects.filter(family=request.user).select_related(
            "senior", "permissions"
        )
    else:
        return HttpResponseForbidden("Esta área é destinada a pessoas idosas e familiares.")
    return render(request, "relationships/list.html", {"links": links})


@login_required
def request_link(request):
    if request.user.role != UserRole.FAMILY:
        return HttpResponseForbidden("Somente familiares podem solicitar este vínculo.")

    form = FamilyLinkRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        senior = form.get_senior()
        if not senior:
            form.add_error(
                "senior_email",
                "Não foi possível solicitar o vínculo. Confira o e-mail informado.",
            )
        else:
            link, created = FamilyLink.objects.get_or_create(
                senior=senior,
                family=request.user,
                defaults={"requested_by": request.user},
            )
            if not created and link.status in {
                FamilyLinkStatus.REJECTED,
                FamilyLinkStatus.REVOKED,
            }:
                link.status = FamilyLinkStatus.PENDING
                link.requested_by = request.user
                link.responded_at = None
                link.save(update_fields=("status", "requested_by", "responded_at"))
                created = True
            if created:
                notify(
                    recipient=senior,
                    kind=NotificationKind.FAMILY_LINK,
                    title="Nova solicitação de vínculo",
                    message=f"{request.user} pediu autorização para acompanhar informações.",
                    target_url=reverse("relationships:list"),
                )
                messages.success(request, "Pedido de autorização enviado para a pessoa idosa.")
            else:
                messages.info(request, "Já existe um vínculo ou solicitação para esse e-mail.")
            return redirect("relationships:list")
    return render(request, "relationships/request.html", {"form": form})


@login_required
@require_POST
def respond_link(request, pk, action):
    if request.user.role != UserRole.SENIOR:
        return HttpResponseForbidden("Somente a pessoa idosa pode responder ao vínculo.")
    link = get_object_or_404(
        FamilyLink,
        pk=pk,
        senior=request.user,
        status=FamilyLinkStatus.PENDING,
    )
    if action not in {"approve", "reject"}:
        return HttpResponseForbidden("Ação inválida.")

    link.status = FamilyLinkStatus.APPROVED if action == "approve" else FamilyLinkStatus.REJECTED
    link.responded_at = timezone.now()
    link.save(update_fields=("status", "responded_at"))
    if action == "approve":
        FamilyPermission.objects.get_or_create(link=link)
    notify(
        recipient=link.family,
        kind=NotificationKind.FAMILY_LINK,
        title="Resposta ao vínculo familiar",
        message=f"Sua solicitação foi {link.get_status_display().lower()} por {request.user}.",
        target_url=reverse("relationships:list"),
    )
    messages.success(request, "Sua resposta foi registrada.")
    return redirect("relationships:list")


@login_required
def edit_permissions(request, pk):
    if request.user.role != UserRole.SENIOR:
        return HttpResponseForbidden("Somente a pessoa idosa controla as permissões.")
    link = get_object_or_404(
        FamilyLink,
        pk=pk,
        senior=request.user,
        status=FamilyLinkStatus.APPROVED,
    )
    permissions, _ = FamilyPermission.objects.get_or_create(link=link)
    form = FamilyPermissionForm(request.POST or None, instance=permissions)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Suas escolhas de compartilhamento foram salvas.")
        return redirect("relationships:list")
    return render(
        request,
        "relationships/permissions.html",
        {"form": form, "link": link},
    )


@login_required
@require_POST
def revoke_link(request, pk):
    if request.user.role != UserRole.SENIOR:
        return HttpResponseForbidden("Somente a pessoa idosa pode revogar o vínculo.")
    link = get_object_or_404(FamilyLink, pk=pk, senior=request.user)
    link.status = FamilyLinkStatus.REVOKED
    link.responded_at = timezone.now()
    link.save(update_fields=("status", "responded_at"))
    notify(
        recipient=link.family,
        kind=NotificationKind.FAMILY_LINK,
        title="Vínculo encerrado",
        message=f"{request.user} encerrou o vínculo familiar.",
        target_url=reverse("relationships:list"),
    )
    return redirect("relationships:list")


@login_required
def senior_overview(request, pk):
    if request.user.role != UserRole.FAMILY:
        return HttpResponseForbidden("Somente familiares autorizados acessam esta área.")
    link = get_object_or_404(
        FamilyLink.objects.select_related("senior", "permissions"),
        pk=pk,
        family=request.user,
        status=FamilyLinkStatus.APPROVED,
    )
    permissions = link.permissions
    context = {"link": link, "permissions": permissions}
    if permissions.can_view_needs:
        context["needs"] = link.senior.needs.all()
    if permissions.can_view_requests:
        context["help_requests"] = HelpRequest.objects.filter(
            need__senior=link.senior
        ).select_related("need", "created_by")
    if permissions.can_view_professional_interests:
        context["professional_interests"] = ProfessionalInterest.objects.filter(
            help_request__need__senior=link.senior
        ).select_related("help_request__need", "professional", "professional__professional_profile")
    return render(request, "relationships/senior_overview.html", context)
