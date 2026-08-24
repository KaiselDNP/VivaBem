from django.contrib import admin

from .models import ChatBlock, ChatModerationEvent, Conversation


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("participant_one", "participant_two", "updated_at")
    search_fields = ("participant_one__email", "participant_two__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ChatModerationEvent)
class ChatModerationEventAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "matched_categories", "message_length", "created_at")
    list_filter = ("matched_categories", "created_at")
    search_fields = ("sender__email", "recipient__email")
    readonly_fields = (
        "conversation",
        "sender",
        "recipient",
        "matched_categories",
        "message_length",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ChatBlock)
class ChatBlockAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked", "created_at")
    search_fields = ("blocker__email", "blocked__email")
    readonly_fields = ("blocker", "blocked", "created_at")

    def has_add_permission(self, request):
        return False
