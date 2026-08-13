import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import UserRole


class Command(BaseCommand):
    help = "Cria a primeira conta administrativa usando variáveis de ambiente."

    def handle(self, *args, **options):
        email = os.getenv("VIVABEM_ADMIN_EMAIL", "").strip().lower()
        password = os.getenv("VIVABEM_ADMIN_PASSWORD", "")
        if not email or not password:
            self.stdout.write("Conta administrativa inicial não configurada; etapa ignorada.")
            return

        user_model = get_user_model()
        existing = user_model.objects.filter(email__iexact=email).first()
        if existing:
            if not existing.is_superuser or existing.role != UserRole.ADMIN:
                raise CommandError("O e-mail informado já pertence a uma conta não administrativa.")
            self.stdout.write("A conta administrativa inicial já existe.")
            return

        user = user_model(
            email=email,
            first_name="Administrador",
            role=UserRole.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        validate_password(password, user=user)
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS("Conta administrativa inicial criada."))
