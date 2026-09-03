import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.chat.models import ChatMessage, Conversation
from apps.moderation.models import AdminAnnouncement, Report, ReportCategory
from apps.needs.models import (
    HelpRequest,
    HelpRequestStatus,
    InterestStatus,
    Need,
    NeedCategory,
    ProfessionalInterest,
    RequestPriority,
)
from apps.notifications.models import Notification, NotificationKind
from apps.professionals.models import ProfessionalProfile, ServiceMode, VerificationStatus
from apps.profiles.models import UserProfile
from apps.relationships.models import FamilyLink, FamilyLinkStatus, FamilyPermission

DEMO_DOMAIN = "demo.vivabem.test"
DEFAULT_DEMO_PASSWORD = "VivaBemTeste2026!"


class Command(BaseCommand):
    help = "Cria contas e dados fictícios reproduzíveis para desenvolvimento local."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Apaga somente as contas @demo.vivabem.test antes de recriar os dados.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Os dados fictícios só podem ser criados com DEBUG=true.")

        password = os.getenv("VIVABEM_DEMO_PASSWORD", DEFAULT_DEMO_PASSWORD)
        sample_user = get_user_model()(email=f"teste@{DEMO_DOMAIN}")
        validate_password(password, user=sample_user)

        with transaction.atomic():
            if options["reset"]:
                deleted = self._reset_demo_data()
                self.stdout.write(f"Registros fictícios removidos: {deleted}.")

            users = self._create_users(password)
            self._create_profiles(users)
            self._create_scenario(users)

        self.stdout.write(self.style.SUCCESS("Dados locais de demonstração estão prontos."))
        self.stdout.write("Contas: idoso, familiar e profissional @demo.vivabem.test")
        self.stdout.write(
            "Senha: valor de VIVABEM_DEMO_PASSWORD ou a senha de demonstração documentada."
        )

    def _reset_demo_data(self):
        demo_users = get_user_model().objects.filter(email__iendswith=f"@{DEMO_DOMAIN}")
        AdminAnnouncement.objects.filter(created_by__in=demo_users).delete()
        Report.objects.filter(reporter__in=demo_users).delete()
        HelpRequest.objects.filter(need__senior__in=demo_users).delete()
        Need.objects.filter(senior__in=demo_users).delete()
        FamilyLink.objects.filter(
            Q(senior__in=demo_users)
            | Q(family__in=demo_users)
            | Q(requested_by__in=demo_users)
        ).delete()
        deleted, _ = demo_users.delete()
        return deleted

    def _upsert_user(self, *, email, password, first_name, last_name, role, is_staff=False):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(email=email)
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.is_active = True
        user.is_staff = is_staff
        user.is_superuser = is_staff
        user.accepted_terms_at = user.accepted_terms_at or timezone.now()
        user.set_password(password)
        user.full_clean(exclude={"password"})
        user.save()
        return user

    def _create_users(self, password):
        return {
            "senior": self._upsert_user(
                email=f"idoso@{DEMO_DOMAIN}",
                password=password,
                first_name="Cleide",
                last_name="Demonstração",
                role=UserRole.SENIOR,
            ),
            "family": self._upsert_user(
                email=f"familiar@{DEMO_DOMAIN}",
                password=password,
                first_name="Guilherme",
                last_name="Demonstração",
                role=UserRole.FAMILY,
            ),
            "professional": self._upsert_user(
                email=f"profissional@{DEMO_DOMAIN}",
                password=password,
                first_name="Ana",
                last_name="Demonstração",
                role=UserRole.PROFESSIONAL,
            ),
        }

    def _create_profiles(self, users):
        UserProfile.objects.update_or_create(
            user=users["senior"],
            defaults={"city": "Avaré", "neighborhood": "Centro"},
        )
        UserProfile.objects.update_or_create(
            user=users["family"],
            defaults={"city": "Avaré", "neighborhood": "Centro"},
        )
        UserProfile.objects.update_or_create(
            user=users["professional"],
            defaults={"city": "Avaré", "bio": "Perfil fictício para testar o VivaBem."},
        )
        ProfessionalProfile.objects.update_or_create(
            user=users["professional"],
            defaults={
                "profession": "Profissional de apoio",
                "specialty": "Acompanhamento e inclusão digital",
                "service_region": "Avaré-SP",
                "service_mode": ServiceMode.BOTH,
                "verification_status": VerificationStatus.PENDING,
                "verification_notes": "Cadastro fictício para testes locais.",
            },
        )

    def _create_scenario(self, users):
        link, _ = FamilyLink.objects.update_or_create(
            senior=users["senior"],
            family=users["family"],
            defaults={
                "requested_by": users["family"],
                "status": FamilyLinkStatus.APPROVED,
                "responded_at": timezone.now(),
            },
        )
        FamilyPermission.objects.update_or_create(
            link=link,
            defaults={
                "can_view_needs": True,
                "can_view_requests": True,
                "can_view_professional_interests": True,
                "can_receive_notifications": True,
                "can_create_requests": True,
            },
        )

        need, _ = Need.objects.update_or_create(
            senior=users["senior"],
            title="Ajuda com o celular",
            defaults={
                "category": NeedCategory.DIGITAL,
                "description": "Preciso de ajuda para organizar os aplicativos do celular.",
            },
        )
        help_request = HelpRequest.objects.filter(need=need).first()
        if help_request is None:
            help_request = HelpRequest(need=need)
        help_request.created_by = users["senior"]
        help_request.details = "Gostaria de receber orientação em um horário combinado."
        help_request.region = "Avaré-SP"
        help_request.priority = RequestPriority.ROUTINE
        help_request.preferred_service_mode = ServiceMode.BOTH
        help_request.status = HelpRequestStatus.ACCEPTED
        help_request.save()

        ProfessionalInterest.objects.update_or_create(
            help_request=help_request,
            professional=users["professional"],
            defaults={
                "message": "Posso ajudar com essa solicitação.",
                "status": InterestStatus.ACCEPTED,
                "responded_at": timezone.now(),
            },
        )

        participant_one, participant_two = sorted(
            (users["senior"], users["professional"]), key=lambda user: user.pk
        )
        conversation, _ = Conversation.objects.get_or_create(
            participant_one=participant_one,
            participant_two=participant_two,
        )
        ChatMessage.objects.get_or_create(
            conversation=conversation,
            sender=users["professional"],
            body="Olá! Esta é uma conversa fictícia para testar o sistema.",
        )

        Notification.objects.update_or_create(
            recipient=users["senior"],
            kind=NotificationKind.INTEREST_RESPONSE,
            title="Profissional escolhido",
            defaults={
                "message": "Seu pedido fictício já possui um profissional escolhido.",
                "target_url": reverse("needs:request_detail", args=(help_request.pk,)),
            },
        )
        Report.objects.update_or_create(
            reporter=users["family"],
            subject="Teste da área de denúncias",
            defaults={
                "reported_user": None,
                "category": ReportCategory.TECHNICAL,
                "description": "Relato fictício criado somente para testar a administração.",
            },
        )
