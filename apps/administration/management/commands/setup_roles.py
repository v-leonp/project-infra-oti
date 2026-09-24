from django.core.management.base import BaseCommand

from apps.administration.role_setup import setup_roles_and_permissions


class Command(BaseCommand):
    help = "Crea grupos Administrador/Usuario y permisos por defecto (idempotente)."

    def handle(self, *args, **options):
        setup_roles_and_permissions()
        self.stdout.write(self.style.SUCCESS("Roles y permisos configurados correctamente."))
