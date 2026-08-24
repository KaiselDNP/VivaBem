from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChatMessageForm
from .models import ChatBlock, Conversation
from .moderation import record_blocked_message
from .services import (
    available_chat_contacts,
    can_users_chat,
    get_or_create_conversation,
    relationship_allows_chat,
)

MESSAGE_RATE_LIMIT = 10


@login_required
def conversation_list(request):
    conversations = (
        Conversation.objects.filter(
            Q(participant_one=request.user) | Q(participant_two=request.user)
        )
        .select_related("participant_one", "participant_two")
        .prefetch_related("messages")
    )
    conversation_items = []
    existing_contact_ids = set()
    for conversation in conversations:
        other = conversation.other_participant(request.user)
        if not relationship_allows_chat(request.user, other):
            continue
        message_list = list(conversation.messages.all())
        conversation_items.append(
            {
                "conversation": conversation,
                "other": other,
                "last_message": message_list[-1] if message_list else None,
                "unread_count": sum(
                    1
                    for item in message_list
                    if item.sender_id != request.user.pk and item.read_at is None
                ),
            }
        )
        existing_contact_ids.add(other.pk)
    contacts = available_chat_contacts(request.user).exclude(pk__in=existing_contact_ids)
    return render(
        request,
        "chat/list.html",
        {"conversation_items": conversation_items, "contacts": contacts},
    )


@login_required
@require_POST
def conversation_start(request, user_id):
    other = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
    if not can_users_chat(request.user, other):
        return HttpResponseForbidden("Não existe autorização para iniciar esta conversa.")
    conversation, _ = get_or_create_conversation(request.user, other)
    return redirect("chat:detail", pk=conversation.pk)


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("participant_one", "participant_two"),
        Q(participant_one=request.user) | Q(participant_two=request.user),
        pk=pk,
    )
    other = conversation.other_participant(request.user)
    if not relationship_allows_chat(request.user, other):
        return HttpResponseForbidden("A autorização desta conversa não está mais ativa.")

    blocked_by_me = ChatBlock.objects.filter(blocker=request.user, blocked=other).exists()
    blocked_by_other = ChatBlock.objects.filter(blocker=other, blocked=request.user).exists()

    conversation.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(
        read_at=timezone.now()
    )

    form = ChatMessageForm(request.POST or None)
    if request.method == "POST":
        if blocked_by_me or blocked_by_other:
            messages.error(request, "Esta conversa está bloqueada e não aceita novas mensagens.")
            return redirect("chat:detail", pk=conversation.pk)
        if form.is_valid():
            sent_since = timezone.now() - timedelta(minutes=1)
            if (
                conversation.messages.filter(
                    sender=request.user,
                    created_at__gte=sent_since,
                ).count()
                >= MESSAGE_RATE_LIMIT
            ):
                messages.error(
                    request,
                    "Muitas mensagens foram enviadas em pouco tempo. Aguarde um minuto.",
                )
                return redirect("chat:detail", pk=conversation.pk)
            chat_message = form.save(commit=False)
            chat_message.conversation = conversation
            chat_message.sender = request.user
            chat_message.full_clean()
            chat_message.save()
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=("updated_at",))
            messages.success(request, "Mensagem enviada.")
            return redirect("chat:detail", pk=conversation.pk)

        moderation_result = getattr(form, "moderation_result", None)
        if moderation_result and moderation_result.blocked:
            record_blocked_message(
                conversation=conversation,
                sender=request.user,
                recipient=other,
                result=moderation_result,
                message_length=len(request.POST.get("body", "")),
            )
            messages.error(
                request,
                "Mensagem removida por possível uso indevido. A administração foi avisada.",
            )
            return redirect("chat:detail", pk=conversation.pk)

    return render(
        request,
        "chat/detail.html",
        {
            "conversation": conversation,
            "other": other,
            "chat_messages": conversation.messages.select_related("sender"),
            "form": form,
            "blocked_by_me": blocked_by_me,
            "blocked_by_other": blocked_by_other,
        },
    )


@login_required
def conversation_messages(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("participant_one", "participant_two"),
        Q(participant_one=request.user) | Q(participant_two=request.user),
        pk=pk,
    )
    other = conversation.other_participant(request.user)
    if not relationship_allows_chat(request.user, other):
        return HttpResponseForbidden("A autorização desta conversa não está mais ativa.")

    after = request.GET.get("after", "0")
    after_id = int(after) if after.isdigit() else 0
    new_messages = list(
        conversation.messages.filter(pk__gt=after_id).select_related("sender")[:100]
    )
    incoming_ids = [item.pk for item in new_messages if item.sender_id != request.user.pk]
    if incoming_ids:
        conversation.messages.filter(pk__in=incoming_ids, read_at__isnull=True).update(
            read_at=timezone.now()
        )
    return JsonResponse(
        {
            "messages": [
                {
                    "id": item.pk,
                    "body": item.body,
                    "created_at": timezone.localtime(item.created_at).strftime("%d/%m/%Y %H:%M"),
                    "is_own": item.sender_id == request.user.pk,
                    "sender": item.sender.get_full_name() or item.sender.email,
                }
                for item in new_messages
            ]
        }
    )


def _conversation_for_action(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("participant_one", "participant_two"),
        Q(participant_one=request.user) | Q(participant_two=request.user),
        pk=pk,
    )
    other = conversation.other_participant(request.user)
    if not relationship_allows_chat(request.user, other):
        return None, None
    return conversation, other


@login_required
@require_POST
def conversation_block(request, pk):
    conversation, other = _conversation_for_action(request, pk)
    if not conversation:
        return HttpResponseForbidden("Esta conversa não pode ser alterada.")
    ChatBlock.objects.get_or_create(blocker=request.user, blocked=other)
    messages.success(
        request,
        (
            f"{other.get_full_name() or other.email} foi bloqueado. "
            "Novas mensagens foram interrompidas."
        ),
    )
    return redirect("chat:detail", pk=conversation.pk)


@login_required
@require_POST
def conversation_unblock(request, pk):
    conversation, other = _conversation_for_action(request, pk)
    if not conversation:
        return HttpResponseForbidden("Esta conversa não pode ser alterada.")
    ChatBlock.objects.filter(blocker=request.user, blocked=other).delete()
    messages.success(request, "Conta desbloqueada. A conversa pode continuar.")
    return redirect("chat:detail", pk=conversation.pk)
