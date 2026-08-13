from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User, UserRole
from apps.notifications.models import Notification, NotificationKind
from apps.notifications.services import notify
from apps.professionals.models import ProfessionalProfile, VerificationStatus

from .forms import AdminAnnouncementForm, ProfessionalReviewForm, ReportForm, ReportReviewForm
from .models import (
    AdminAnnouncement,
    AdminAuditLog,
    AnnouncementAudience,
    AuditAction,
    Report,
    ReportStatus,
)
from .services import record_admin_action


def administration_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        has_access = request.user.is_superuser or (
            request.user.is_staff and request.user.role == UserRole.ADMIN
        )
        if not has_access:
            return HttpResponseForbidden("Acesso restrito à administração do VivaBem.")
        return view_func(request, *args, **kwargs)

    return wrapped


@login_required
def report_list(request):
    reports = Report.objects.filter(reporter=request.user).select_related("reported_user")
    return render(request, "moderation/report_list.html", {"reports": reports})


@login_required
def report_create(request):
    target_id = request.GET.get("usuario", "").strip()
    reported_user = None
    if target_id.isdigit():
        reported_user = (
            User.objects.filter(pk=target_id, is_active=True).exclude(pk=request.user.pk).first()
        )

    form = ReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.reported_user = reported_user
        report.save()
        messages.success(
            request,
            "Denúncia enviada. A administração poderá atualizar o andamento por aqui.",
        )
        return redirect("moderation:report_detail", pk=report.pk)
    return render(
        request,
        "moderation/report_form.html",
        {"form": form, "reported_user": reported_user},
    )


@login_required
def report_detail(request, pk):
    report = get_object_or_404(
        Report.objects.select_related("reported_user"),
        pk=pk,
        reporter=request.user,
    )
    return render(request, "moderation/report_detail.html", {"report": report})


@administration_required
def administration_dashboard(request):
    report_counts = Report.objects.aggregate(
        open=Count("id", filter=Q(status=ReportStatus.OPEN)),
        in_review=Count("id", filter=Q(status=ReportStatus.IN_REVIEW)),
    )
    context = {
        "report_counts": report_counts,
        "pending_professionals": ProfessionalProfile.objects.filter(
            verification_status=VerificationStatus.PENDING
        ).count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "recent_reports": Report.objects.select_related("reporter")[:6],
        "recent_actions": AdminAuditLog.objects.select_related("actor")[:6],
    }
    return render(request, "moderation/admin_dashboard.html", context)


@administration_required
def administration_reports(request):
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    reports = Report.objects.select_related("reporter", "reported_user", "assigned_to")
    if status in ReportStatus.values:
        reports = reports.filter(status=status)
    if query:
        reports = reports.filter(
            Q(subject__icontains=query)
            | Q(description__icontains=query)
            | Q(reporter__first_name__icontains=query)
            | Q(reporter__last_name__icontains=query)
        )
    return render(
        request,
        "moderation/admin_reports.html",
        {
            "reports": reports[:100],
            "status": status,
            "query": query,
            "statuses": ReportStatus.choices,
        },
    )


@administration_required
@transaction.atomic
def administration_report_review(request, pk):
    report = get_object_or_404(
        Report.objects.select_for_update(),
        pk=pk,
    )
    form = ReportReviewForm(request.POST or None, instance=report)
    if request.method == "POST" and form.is_valid():
        previous_status = report.status
        report = form.save(commit=False)
        report.assigned_to = request.user
        report.resolved_at = (
            timezone.now()
            if report.status in {ReportStatus.RESOLVED, ReportStatus.DISMISSED}
            else None
        )
        report.save()
        record_admin_action(
            actor=request.user,
            action=AuditAction.REPORT_REVIEW,
            target=report,
            target_type="report",
            description=f"Status alterado de {previous_status} para {report.status}.",
        )
        notify(
            recipient=report.reporter,
            kind=NotificationKind.REPORT_UPDATE,
            title="Denúncia atualizada",
            message=(
                f"A denúncia #{report.pk} agora está como {report.get_status_display().lower()}."
            ),
            target_url=reverse("moderation:report_detail", args=(report.pk,)),
        )
        messages.success(request, "Análise registrada e usuário notificado.")
        return redirect("moderation:admin_reports")
    return render(
        request,
        "moderation/admin_report_review.html",
        {"report": report, "form": form},
    )


@administration_required
def administration_professionals(request):
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    profiles = ProfessionalProfile.objects.select_related("user", "verified_by")
    if status in VerificationStatus.values:
        profiles = profiles.filter(verification_status=status)
    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(profession__icontains=query)
            | Q(specialty__icontains=query)
            | Q(registration_number__icontains=query)
        )
    return render(
        request,
        "moderation/admin_professionals.html",
        {
            "professionals": profiles[:100],
            "status": status,
            "query": query,
            "statuses": VerificationStatus.choices,
        },
    )


@administration_required
@transaction.atomic
def administration_professional_review(request, pk):
    profile = get_object_or_404(
        ProfessionalProfile.objects.select_for_update().select_related("user"),
        pk=pk,
    )
    form = ProfessionalReviewForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        previous_status = profile.verification_status
        profile = form.save(commit=False)
        if profile.verification_status == VerificationStatus.VERIFIED:
            profile.verified_at = timezone.now()
            profile.verified_by = request.user
        else:
            profile.verified_at = None
            profile.verified_by = None
        profile.save()
        record_admin_action(
            actor=request.user,
            action=AuditAction.PROFESSIONAL_REVIEW,
            target=profile,
            target_type="professional_profile",
            description=f"Status alterado de {previous_status} para {profile.verification_status}.",
        )
        notify(
            recipient=profile.user,
            kind=NotificationKind.PROFESSIONAL_REVIEW,
            title="Perfil profissional analisado",
            message=(
                f"O cadastro agora está como {profile.get_verification_status_display().lower()}."
            ),
            target_url=reverse("accounts:profile_edit"),
        )
        messages.success(request, "Análise profissional registrada.")
        return redirect("moderation:admin_professionals")
    return render(
        request,
        "moderation/admin_professional_review.html",
        {"profile": profile, "form": form},
    )


@administration_required
def administration_users(request):
    role = request.GET.get("role", "").strip()
    query = request.GET.get("q", "").strip()
    users = User.objects.all()
    if role in UserRole.values:
        users = users.filter(role=role)
    if query:
        users = users.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    return render(
        request,
        "moderation/admin_users.html",
        {
            "users": users[:100],
            "role": role,
            "query": query,
            "roles": UserRole.choices,
        },
    )


@administration_required
@transaction.atomic
def administration_announcement_create(request):
    selected_id = request.GET.get("usuario", "").strip()
    selected_user = None
    if selected_id.isdigit():
        selected_user = (
            User.objects.filter(pk=selected_id, is_active=True)
            .exclude(role=UserRole.ADMIN)
            .exclude(is_superuser=True)
            .first()
        )
    form = AdminAnnouncementForm(request.POST or None, selected_user=selected_user)
    if request.method == "POST" and form.is_valid():
        announcement = form.save(commit=False)
        announcement.created_by = request.user
        announcement.save()

        recipients = (
            User.objects.filter(is_active=True)
            .exclude(role=UserRole.ADMIN)
            .exclude(is_superuser=True)
        )
        if announcement.audience == AnnouncementAudience.INDIVIDUAL:
            recipients = recipients.filter(pk=announcement.recipient_id)
        elif announcement.audience != AnnouncementAudience.ALL_USERS:
            recipients = recipients.filter(role=announcement.audience)

        recipient_ids = list(recipients.values_list("pk", flat=True))
        Notification.objects.bulk_create(
            [
                Notification(
                    recipient_id=recipient_id,
                    kind=NotificationKind.ADMIN_NOTICE,
                    title=announcement.title,
                    message=announcement.message,
                    target_url=reverse("notifications:list"),
                )
                for recipient_id in recipient_ids
            ]
        )
        announcement.recipients_count = len(recipient_ids)
        announcement.save(update_fields=("recipients_count",))
        record_admin_action(
            actor=request.user,
            action=AuditAction.NOTICE_SENT,
            target=announcement,
            target_type="admin_announcement",
            description=(
                f"Aviso enviado para {announcement.recipients_count} conta(s): "
                f"{announcement.get_audience_display()}."
            ),
        )
        messages.success(
            request,
            f"Aviso enviado para {announcement.recipients_count} conta(s).",
        )
        return redirect("moderation:admin_announcements")
    return render(
        request,
        "moderation/admin_announcement_form.html",
        {"form": form, "selected_user": selected_user},
    )


@administration_required
def administration_announcements(request):
    announcements = AdminAnnouncement.objects.select_related("created_by", "recipient")[:100]
    return render(
        request,
        "moderation/admin_announcements.html",
        {"announcements": announcements},
    )


@administration_required
@require_POST
@transaction.atomic
def administration_user_status(request, pk, action):
    user = get_object_or_404(User.objects.select_for_update(), pk=pk)
    if action not in {"activate", "deactivate"}:
        return HttpResponseForbidden("Ação inválida.")
    if user.pk == request.user.pk or user.role == UserRole.ADMIN or user.is_superuser:
        return HttpResponseForbidden("Contas administrativas não podem ser alteradas aqui.")
    user.is_active = action == "activate"
    user.save(update_fields=("is_active",))
    record_admin_action(
        actor=request.user,
        action=AuditAction.USER_STATUS,
        target=user,
        target_type="user",
        description="Conta ativada." if user.is_active else "Conta desativada.",
    )
    notify(
        recipient=user,
        kind=NotificationKind.ACCOUNT_STATUS,
        title="Situação da conta atualizada",
        message="Sua conta foi ativada." if user.is_active else "Sua conta foi desativada.",
    )
    messages.success(request, "Situação da conta atualizada.")
    return redirect("moderation:admin_users")


@administration_required
def administration_audit(request):
    logs = AdminAuditLog.objects.select_related("actor")[:200]
    return render(request, "moderation/admin_audit.html", {"logs": logs})
