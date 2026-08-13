from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "kind", "title", "read_at", "created_at")
    list_filter = ("kind", "read_at", "created_at")
    search_fields = ("recipient__email", "title", "message")
    readonly_fields = ("created_at",)
