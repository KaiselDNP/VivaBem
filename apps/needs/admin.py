from django.contrib import admin

from .models import HelpRequest, Need, ProfessionalInterest


@admin.register(Need)
class NeedAdmin(admin.ModelAdmin):
    list_display = ("title", "senior", "category", "status", "created_at")
    list_filter = ("category", "status", "created_at")
    search_fields = ("title", "description", "senior__email")


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ("need", "region", "priority", "status", "created_at")
    list_filter = ("status", "priority", "preferred_service_mode")
    search_fields = ("need__title", "need__senior__email", "details", "region")


@admin.register(ProfessionalInterest)
class ProfessionalInterestAdmin(admin.ModelAdmin):
    list_display = ("professional", "help_request", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("professional__email", "help_request__need__title")
