from django.db.models import Q

from apps.accounts.models import UserRole
from apps.needs.models import InterestStatus, ProfessionalInterest
from apps.relationships.models import FamilyLink, FamilyLinkStatus

from .models import ChatBlock, Conversation


def _senior_family_can_chat(senior, family):
    return FamilyLink.objects.filter(
        senior=senior,
        family=family,
        status=FamilyLinkStatus.APPROVED,
    ).exists()


def _senior_professional_can_chat(senior, professional):
    return ProfessionalInterest.objects.filter(
        professional=professional,
        status=InterestStatus.ACCEPTED,
        help_request__need__senior=senior,
    ).exists()


def _family_professional_can_chat(family, professional):
    return FamilyLink.objects.filter(
        family=family,
        status=FamilyLinkStatus.APPROVED,
        permissions__can_view_professional_interests=True,
        senior__needs__help_requests__professional_interests__professional=professional,
        senior__needs__help_requests__professional_interests__status=InterestStatus.ACCEPTED,
    ).exists()


def relationship_allows_chat(first, second):
    if not first.is_active or not second.is_active or first.pk == second.pk:
        return False
    roles = {first.role, second.role}
    if roles == {UserRole.SENIOR, UserRole.FAMILY}:
        senior = first if first.role == UserRole.SENIOR else second
        family = first if first.role == UserRole.FAMILY else second
        return _senior_family_can_chat(senior, family)
    if roles == {UserRole.SENIOR, UserRole.PROFESSIONAL}:
        senior = first if first.role == UserRole.SENIOR else second
        professional = first if first.role == UserRole.PROFESSIONAL else second
        return _senior_professional_can_chat(senior, professional)
    if roles == {UserRole.FAMILY, UserRole.PROFESSIONAL}:
        family = first if first.role == UserRole.FAMILY else second
        professional = first if first.role == UserRole.PROFESSIONAL else second
        return _family_professional_can_chat(family, professional)
    return False


def is_chat_blocked(first, second):
    return ChatBlock.objects.filter(
        Q(blocker=first, blocked=second) | Q(blocker=second, blocked=first)
    ).exists()


def can_users_chat(first, second):
    return relationship_allows_chat(first, second) and not is_chat_blocked(first, second)


def available_chat_contacts(user):
    user_model = user.__class__
    contacts = user_model.objects.none()
    if user.role == UserRole.SENIOR:
        family_ids = FamilyLink.objects.filter(
            senior=user,
            status=FamilyLinkStatus.APPROVED,
        ).values_list("family_id", flat=True)
        professional_ids = ProfessionalInterest.objects.filter(
            help_request__need__senior=user,
            status=InterestStatus.ACCEPTED,
        ).values_list("professional_id", flat=True)
        contacts = user_model.objects.filter(Q(pk__in=family_ids) | Q(pk__in=professional_ids))
    elif user.role == UserRole.FAMILY:
        links = FamilyLink.objects.filter(
            family=user,
            status=FamilyLinkStatus.APPROVED,
        )
        senior_ids = links.values_list("senior_id", flat=True)
        professional_ids = ProfessionalInterest.objects.filter(
            help_request__need__senior__family_links_as_senior__family=user,
            help_request__need__senior__family_links_as_senior__status=FamilyLinkStatus.APPROVED,
            help_request__need__senior__family_links_as_senior__permissions__can_view_professional_interests=True,
            status=InterestStatus.ACCEPTED,
        ).values_list("professional_id", flat=True)
        contacts = user_model.objects.filter(Q(pk__in=senior_ids) | Q(pk__in=professional_ids))
    elif user.role == UserRole.PROFESSIONAL:
        senior_ids = ProfessionalInterest.objects.filter(
            professional=user,
            status=InterestStatus.ACCEPTED,
        ).values_list("help_request__need__senior_id", flat=True)
        family_ids = FamilyLink.objects.filter(
            senior_id__in=senior_ids,
            status=FamilyLinkStatus.APPROVED,
            permissions__can_view_professional_interests=True,
        ).values_list("family_id", flat=True)
        contacts = user_model.objects.filter(Q(pk__in=senior_ids) | Q(pk__in=family_ids))
    blocked_ids = ChatBlock.objects.filter(blocker=user).values_list("blocked_id", flat=True)
    blocked_by_ids = ChatBlock.objects.filter(blocked=user).values_list("blocker_id", flat=True)
    return (
        contacts.filter(is_active=True)
        .exclude(Q(pk__in=blocked_ids) | Q(pk__in=blocked_by_ids))
        .exclude(pk=user.pk)
        .distinct()
    )


def get_or_create_conversation(first, second):
    first_id, second_id = sorted((first.pk, second.pk))
    return Conversation.objects.get_or_create(
        participant_one_id=first_id,
        participant_two_id=second_id,
    )
