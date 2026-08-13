from django.contrib import admin

from .models import AdminAnnouncement, AdminAuditLog, Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "category", "status", "reporter", "created_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("subject", "description", "reporter__email")
    readonly_fields = ("created_at", "updated_at", "resolved_at")


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_type", "target_label")
    list_filter = ("action", "created_at")
    search_fields = ("target_label", "description", "actor__email")
    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "target_label",
        "description",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdminAnnouncement)
class AdminAnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "audience",
        "recipient",
        "recipients_count",
        "created_by",
        "created_at",
    )
    list_filter = ("audience", "created_at")
    search_fields = ("title", "message", "recipient__email")
    readonly_fields = (
        "created_by",
        "title",
        "message",
        "audience",
        "recipient",
        "recipients_count",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
