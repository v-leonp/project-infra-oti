from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.administration.constants import ROLE_ADMINISTRADOR, SYSTEM_ROLES
from apps.administration.forms import (
    AuditFilterForm,
    GroupPermissionsForm,
    UserCreateForm,
    UserPasswordChangeForm,
    UserSearchForm,
    UserStateConfirmForm,
    UserUpdateForm,
)
from apps.administration.mixins import SystemAdministratorRequiredMixin
from apps.administration.models import GroupProfile
from apps.administration.permissions_registry import iter_matrix_cells
from apps.administration.selectors import audit_log_queryset, user_list_queryset
from apps.administration.services.audit import get_client_ip
from apps.administration.services.groups import (
    GroupPermissionError,
    build_matrix_state,
    update_group_permissions,
)
from apps.administration.services.users import (
    UserAdministrationError,
    create_user,
    get_user_role_name,
    set_user_active_state,
    set_user_password,
    update_user,
)

User = get_user_model()
USERS_PER_PAGE = 10
AUDIT_PER_PAGE = 15


def _htmx_target(request, partial_template: str, full_template: str, context: dict):
    if request.headers.get("HX-Request"):
        return render(request, partial_template, context)
    return render(request, full_template, context)


class UserListView(SystemAdministratorRequiredMixin, View):
    template_name = "administration/users/list.html"
    partial_template = "administration/users/_table.html"

    def get(self, request):
        form = UserSearchForm(request.GET)
        search = form.data.get("q", "") if form.is_bound else ""
        role = form.data.get("role", "") if form.is_bound else ""
        status = form.data.get("status", "") if form.is_bound else ""
        queryset = user_list_queryset(search=search, role=role, status=status)
        paginator = Paginator(queryset, USERS_PER_PAGE)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "form": form,
            "page_obj": page_obj,
            "users": page_obj.object_list,
            "total_count": paginator.count,
        }
        return _htmx_target(request, self.partial_template, self.template_name, context)


class UserCreateView(SystemAdministratorRequiredMixin, FormView):
    template_name = "administration/users/create.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("administration:user_list")

    def form_valid(self, form):
        try:
            create_user(
                actor=self.request.user,
                username=form.cleaned_data["username"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                password=form.cleaned_data["password1"],
                is_active=form.cleaned_data.get("is_active", True),
                ip_address=get_client_ip(self.request),
            )
        except UserAdministrationError as exc:
            if hasattr(exc, "error_dict"):
                for field, errs in exc.error_dict.items():
                    form.add_error(field if field in form.fields else None, errs)
                return self.form_invalid(form)
            form.add_error(None, exc.messages[0])
            return self.form_invalid(form)
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)


class UserDetailView(SystemAdministratorRequiredMixin, TemplateView):
    template_name = "administration/users/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, pk=self.kwargs["pk"])
        context["profile_user"] = user
        context["role_name"] = get_user_role_name(user)
        return context


class UserUpdateView(SystemAdministratorRequiredMixin, FormView):
    template_name = "administration/users/edit.html"
    form_class = UserUpdateForm

    def dispatch(self, request, *args, **kwargs):
        self.profile_user = get_object_or_404(User, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        role = get_user_role_name(self.profile_user) or ROLE_ADMINISTRADOR
        return {
            "first_name": self.profile_user.first_name,
            "last_name": self.profile_user.last_name,
            "email": self.profile_user.email,
            "role": role,
            "is_active": self.profile_user.is_active,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.profile_user
        return kwargs

    def form_valid(self, form):
        try:
            update_user(
                actor=self.request.user,
                user=self.profile_user,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                is_active=form.cleaned_data["is_active"],
                ip_address=get_client_ip(self.request),
            )
        except UserAdministrationError as exc:
            if hasattr(exc, "error_dict"):
                for field, errs in exc.error_dict.items():
                    form.add_error(field if field in form.fields else None, errs)
                return self.form_invalid(form)
            form.add_error(None, exc.messages[0])
            return self.form_invalid(form)
        messages.success(self.request, "Usuario actualizado correctamente.")
        return redirect("administration:user_detail", pk=self.profile_user.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.profile_user
        context["password_form"] = UserPasswordChangeForm()
        return context

    def post(self, request, *args, **kwargs):
        if "change_password" in request.POST:
            return self._handle_password_change(request)
        return super().post(request, *args, **kwargs)

    def _handle_password_change(self, request):
        password_form = UserPasswordChangeForm(request.POST)
        if password_form.is_valid():
            set_user_password(
                actor=request.user,
                user=self.profile_user,
                password=password_form.cleaned_data["password1"],
                ip_address=get_client_ip(request),
            )
            messages.success(request, "Contraseña actualizada correctamente.")
            return redirect("administration:user_edit", pk=self.profile_user.pk)
        form = self.get_form()
        return render(
            request,
            self.template_name,
            {"form": form, "password_form": password_form, "profile_user": self.profile_user},
        )


class UserStateChangeView(SystemAdministratorRequiredMixin, FormView):
    template_name = "administration/users/confirm_state.html"
    form_class = UserStateConfirmForm

    def dispatch(self, request, *args, **kwargs):
        self.profile_user = get_object_or_404(User, pk=kwargs["pk"])
        self.activate = request.GET.get("action") == "activate"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.profile_user
        context["activate"] = self.activate
        return context

    def form_valid(self, form):
        self.activate = self.request.POST.get("state_action") == "activate"
        try:
            set_user_active_state(
                actor=self.request.user,
                user=self.profile_user,
                activate=self.activate,
                ip_address=get_client_ip(self.request),
            )
        except UserAdministrationError as exc:
            form.add_error(None, exc.messages[0])
            return self.form_invalid(form)
        verb = "reactivado" if self.activate else "desactivado"
        messages.success(self.request, f"Usuario {verb} correctamente.")
        return redirect("administration:user_list")


class GroupPermissionsView(SystemAdministratorRequiredMixin, View):
    template_name = "administration/groups/permissions.html"

    def get_group(self, request):
        group_id = request.GET.get("group") or request.POST.get("group")
        if group_id:
            return get_object_or_404(Group, pk=group_id, name__in=SYSTEM_ROLES)
        return Group.objects.get(name=ROLE_ADMINISTRADOR)

    def get_permission_choices(self):
        choices = []
        for module, action, codename in iter_matrix_cells():
            choices.append((codename, f"{module['label']} — {action}"))
        return choices

    def get(self, request):
        group = self.get_group(request)
        profile = GroupProfile.objects.filter(group=group).first()
        matrix = build_matrix_state(group)
        selected = list(matrix["assigned"])
        form = GroupPermissionsForm(
            initial={
                "group": group,
                "description": profile.description if profile else "",
                "permissions": selected,
                "active_tab": request.GET.get("tab", "permissions"),
            },
            permission_choices=self.get_permission_choices(),
        )
        members = group.user_set.all().order_by("username")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "group": group,
                "matrix_rows": matrix["rows"],
                "members": members,
                "groups": Group.objects.filter(name__in=SYSTEM_ROLES),
                "active_tab": request.GET.get("tab", "permissions"),
            },
        )

    def post(self, request):
        group = self.get_group(request)
        form = GroupPermissionsForm(request.POST, permission_choices=self.get_permission_choices())
        if form.is_valid():
            selected_codenames = set(request.POST.getlist("permissions"))
            try:
                update_group_permissions(
                    actor=request.user,
                    group=group,
                    description=form.cleaned_data["description"],
                    selected_codenames=selected_codenames,
                    ip_address=get_client_ip(request),
                )
                messages.success(request, "Permisos guardados correctamente.")
                return redirect(f"{reverse('administration:group_permissions')}?group={group.pk}")
            except GroupPermissionError as exc:
                form.add_error(None, exc.messages[0])
        matrix = build_matrix_state(group)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "group": group,
                "matrix_rows": matrix["rows"],
                "members": group.user_set.all().order_by("username"),
                "groups": Group.objects.filter(name__in=SYSTEM_ROLES),
                "active_tab": request.POST.get("active_tab", "permissions"),
            },
        )


class AuditLogListView(SystemAdministratorRequiredMixin, View):
    template_name = "administration/audit/list.html"
    partial_template = "administration/audit/_table.html"

    def get(self, request):
        form = AuditFilterForm(request.GET)
        date_from = date_to = None
        actor = target_user = None
        action = ""
        if form.is_valid():
            date_from = form.cleaned_data.get("date_from")
            date_to = form.cleaned_data.get("date_to")
            actor = form.cleaned_data.get("actor")
            action = form.cleaned_data.get("action") or ""
            target_user = form.cleaned_data.get("target_user")

        queryset = audit_log_queryset(
            date_from=date_from,
            date_to=date_to,
            actor_id=actor.pk if actor else None,
            action=action,
            target_user_id=target_user.pk if target_user else None,
        )
        paginator = Paginator(queryset, AUDIT_PER_PAGE)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {"form": form, "page_obj": page_obj, "logs": page_obj.object_list}
        return _htmx_target(request, self.partial_template, self.template_name, context)
