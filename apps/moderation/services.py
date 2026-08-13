from .models import AdminAuditLog


def record_admin_action(*, actor, action, target, target_type, description):
    return AdminAuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target.pk,
        target_label=str(target)[:150],
        description=description[:500],
    )
