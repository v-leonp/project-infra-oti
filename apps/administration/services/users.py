from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.administration.constants import (
    AUDIT_ROLE_CHANGED,
    AUDIT_USER_ACTIVATED,
    AUDIT_USER_CREATED,
    AUDIT_USER_DEACTIVATED,
    AUDIT_USER_UPDATED,
    ROLE_ADMINISTRADOR,
    ROLE_USUARIO,
    SYSTEM_ROLES,
)
from apps.administration.role_setup import ensure_system_groups
from apps.administration.services.audit import log_audit_event, user_snapshot

User = get_user_model()


class UserAdministrationError(ValidationError):
    pass


def get_user_role_name(user: User) -> str | None:
    group = user.groups.filter(name__in=SYSTEM_ROLES).first()
    return group.name if group else None


def count_active_administrators(exclude_pk: int | None = None) -> int:
    qs = User.objects.filter(is_active=True, groups__name=ROLE_ADMINISTRADOR).distinct()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.count()


def _assign_single_role(user: User, role_name: str) -> None:
    if role_name not in SYSTEM_ROLES:
        raise UserAdministrationError("Rol no válido.")
    groups = ensure_system_groups()
    user.groups.set([groups[role_name]])


def _validate_last_administrator(user: User, new_role: str | None, will_be_active: bool) -> None:
    is_admin = get_user_role_name(user) == ROLE_ADMINISTRADOR
    if not is_admin:
        return
    if new_role == ROLE_USUARIO or will_be_active is False:
        if count_active_administrators(exclude_pk=user.pk) == 0:
            raise UserAdministrationError(
                "No puede desactivar ni cambiar el rol del último Administrador activo."
            )


@transaction.atomic
def create_user(
    *,
    actor: User,
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    role: str,
    password: str,
    is_active: bool,
    ip_address: str | None = None,
) -> User:
    if User.objects.filter(username=username).exists():
        raise UserAdministrationError({"username": "Este nombre de usuario ya está en uso."})
    if User.objects.filter(email__iexact=email).exists():
        raise UserAdministrationError({"email": "Este correo electrónico ya está registrado."})

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
    )
    _assign_single_role(user, role)
    log_audit_event(
        actor=actor,
        action=AUDIT_USER_CREATED,
        target_user=user,
        new_values=user_snapshot(user),
        ip_address=ip_address,
    )
    return user


@transaction.atomic
def update_user(
    *,
    actor: User,
    user: User,
    first_name: str,
    last_name: str,
    email: str,
    role: str,
    is_active: bool,
    ip_address: str | None = None,
) -> User:
    if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
        raise UserAdministrationError({"email": "Este correo electrónico ya está registrado."})

    old_snapshot = user_snapshot(user)
    previous_role = get_user_role_name(user)

    if actor.pk == user.pk and is_active is False:
        raise UserAdministrationError("No puede desactivar su propia cuenta.")

    _validate_last_administrator(user, role, is_active)

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.is_active = is_active
    user.save(update_fields=["first_name", "last_name", "email", "is_active"])

    _assign_single_role(user, role)
    user.refresh_from_db()

    new_snapshot = user_snapshot(user)
    log_audit_event(
        actor=actor,
        action=AUDIT_USER_UPDATED,
        target_user=user,
        old_values=old_snapshot,
        new_values=new_snapshot,
        ip_address=ip_address,
    )
    if previous_role != role:
        log_audit_event(
            actor=actor,
            action=AUDIT_ROLE_CHANGED,
            target_user=user,
            old_values={"role": previous_role},
            new_values={"role": role},
            ip_address=ip_address,
        )
    return user


@transaction.atomic
def set_user_password(
    *,
    actor: User,
    user: User,
    password: str,
    ip_address: str | None = None,
) -> None:
    user.set_password(password)
    user.save(update_fields=["password"])
    log_audit_event(
        actor=actor,
        action=AUDIT_USER_UPDATED,
        target_user=user,
        new_values={"password_changed": True},
        ip_address=ip_address,
    )


@transaction.atomic
def set_user_active_state(
    *,
    actor: User,
    user: User,
    activate: bool,
    ip_address: str | None = None,
) -> User:
    if actor.pk == user.pk and not activate:
        raise UserAdministrationError("No puede desactivar su propia cuenta.")

    _validate_last_administrator(user, get_user_role_name(user), activate)

    old_active = user.is_active
    user.is_active = activate
    user.save(update_fields=["is_active"])

    action = AUDIT_USER_ACTIVATED if activate else AUDIT_USER_DEACTIVATED
    log_audit_event(
        actor=actor,
        action=action,
        target_user=user,
        old_values={"is_active": old_active},
        new_values={"is_active": activate},
        ip_address=ip_address,
    )
    return user
