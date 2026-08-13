from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from .models import ProfessionalProfile, ServiceMode


@login_required
def directory(request):
    query = request.GET.get("q", "").strip()
    mode = request.GET.get("mode", "").strip()
    profiles = (
        ProfessionalProfile.objects.filter(
            user__is_active=True,
        )
        .exclude(profession="")
        .select_related("user")
    )
    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(profession__icontains=query)
            | Q(specialty__icontains=query)
            | Q(service_region__icontains=query)
        )
    if mode in ServiceMode.values:
        profiles = profiles.filter(Q(service_mode=mode) | Q(service_mode=ServiceMode.BOTH))
    return render(
        request,
        "professionals/directory.html",
        {
            "professionals": profiles.order_by("user__first_name")[:100],
            "query": query,
            "mode": mode,
            "service_modes": ServiceMode.choices,
        },
    )
