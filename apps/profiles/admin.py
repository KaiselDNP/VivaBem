from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "neighborhood", "updated_at")
    list_select_related = ("user",)
    search_fields = ("user__email", "user__first_name", "user__last_name", "city")
    readonly_fields = ("updated_at",)
