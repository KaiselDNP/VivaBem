from django.db.models import Q

from .models import ChatMessage


def unread_chat_messages(request):
    if not request.user.is_authenticated:
        return {"unread_chat_count": 0}
    return {
        "unread_chat_count": ChatMessage.objects.filter(
            Q(conversation__participant_one=request.user)
            | Q(conversation__participant_two=request.user),
            read_at__isnull=True,
        )
        .exclude(sender=request.user)
        .count()
    }
