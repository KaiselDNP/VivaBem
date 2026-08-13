from django.contrib import admin

from .models import FamilyLink, FamilyPermission


class FamilyPermissionInline(admin.StackedInline):
    model = FamilyPermission
    extra = 0


@admin.register(FamilyLink)
class FamilyLinkAdmin(admin.ModelAdmin):
    list_display = ("senior", "family", "status", "requested_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("senior__email", "family__email")
    inlines = (FamilyPermissionInline,)
