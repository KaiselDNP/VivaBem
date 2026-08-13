from .models import FamilyLink, FamilyLinkStatus


def authorized_family_users(senior, *permission_names):
    links = FamilyLink.objects.filter(
        senior=senior,
        status=FamilyLinkStatus.APPROVED,
    ).select_related("family", "permissions")
    users = []
    for link in links:
        try:
            permissions = link.permissions
        except AttributeError:
            continue
        if all(getattr(permissions, name, False) for name in permission_names):
            users.append(link.family)
    return users
