from django.contrib import admin
from django.utils import timezone

from .models import ProfessionalProfile, VerificationStatus


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "profession",
        "specialty",
        "service_region",
        "verification_status",
    )
    list_filter = ("verification_status", "service_mode", "profession")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "profession",
        "specialty",
        "registration_number",
    )
    readonly_fields = ("verified_at", "verified_by", "updated_at")
    fieldsets = (
        ("Conta", {"fields": ("user",)}),
        (
            "Dados profissionais",
            {
                "fields": (
                    "profession",
                    "specialty",
                    "council",
                    "registration_number",
                    "service_region",
                    "service_mode",
                )
            },
        ),
        (
            "Verificação administrativa do protótipo",
            {
                "fields": (
                    "verification_status",
                    "verification_notes",
                    "verified_at",
                    "verified_by",
                )
            },
        ),
        ("Controle", {"fields": ("updated_at",)}),
    )

    def save_model(self, request, obj, form, change):
        if obj.verification_status == VerificationStatus.VERIFIED:
            if not obj.verified_at:
                obj.verified_at = timezone.now()
            obj.verified_by = request.user
        else:
            obj.verified_at = None
            obj.verified_by = None
        super().save_model(request, obj, form, change)
