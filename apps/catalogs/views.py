from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.administration.mixins import SystemAdministratorRequiredMixin
from apps.catalogs.constants import CATALOG_PAGE_SIZE
from apps.catalogs.forms import (
    CatalogSearchForm,
    ProviderForm,
    ProviderSearchForm,
    StateConfirmForm,
)
from apps.catalogs.models import Provider, ServiceType
from apps.catalogs.registry import CATALOG_CONFIG, PROVIDER_KEY
from apps.catalogs.selectors import catalog_list_qs
from apps.catalogs.services import (
    CatalogServiceError,
    create_catalog_record,
    set_catalog_active_state,
    update_catalog_record,
)
from apps.catalogs.utils import normalize_name, normalize_whitespace


def _url_stem(catalog_key: str) -> str:
    return catalog_key.replace("-", "_")


def _htmx(request, partial, full, context):
    if request.headers.get("HX-Request"):
        return render(request, partial, context)
    return render(request, full, context)


def _fields_from_form(form, catalog_key: str) -> dict:
    data = form.cleaned_data.copy()
    data.pop("code", None)
    if "name" in data and data["name"]:
        data["name"] = normalize_name(data["name"])
    if catalog_key == "responsables":
        data["first_name"] = normalize_name(data["first_name"])
        data["last_name"] = normalize_name(data["last_name"])
    return data


class ODSOESListView(SystemAdministratorRequiredMixin, View):
    template_name = "catalogs/ods_oes/list.html"
    partial_name = "catalogs/ods_oes/_table.html"

    def get(self, request):
        tab = request.GET.get("tab", "ods")
        if tab not in ("ods", "oes"):
            tab = "ods"
        config = CATALOG_CONFIG[tab]
        form = CatalogSearchForm(request.GET)
        q = form.data.get("q", "") if form.is_bound else ""
        status = form.data.get("status", "") if form.is_bound else ""
        queryset = catalog_list_qs(
            config["model"],
            search=q,
            status=status,
            search_fields=config["search_fields"],
        )
        paginator = Paginator(queryset, CATALOG_PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "tab": tab,
            "url_stem": tab,
            "config": config,
            "form": form,
            "page_obj": page_obj,
            "records": page_obj.object_list,
            "total_count": paginator.count,
            "list_url": reverse("catalogs:ods_oes_list"),
            "create_url": reverse(f"catalogs:{tab}_create"),
        }
        return _htmx(request, self.partial_name, self.template_name, context)


class GenericCatalogFormView(SystemAdministratorRequiredMixin, FormView):
    catalog_key: str = ""
    template_name = "catalogs/generic/form.html"

    def get_form_class(self):
        return CATALOG_CONFIG[self.catalog_key]["form_class"]

    def get_success_url(self):
        if self.catalog_key in ("ods", "oes"):
            return reverse("catalogs:ods_oes_list") + f"?tab={self.catalog_key}"
        return reverse(f"catalogs:{self.catalog_key}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["catalog_key"] = self.catalog_key
        ctx["config"] = CATALOG_CONFIG[self.catalog_key]
        ctx["is_create"] = self.instance is None
        stem = _url_stem(self.catalog_key)
        ctx["url_stem"] = stem
        if self.catalog_key in ("ods", "oes"):
            ctx["cancel_url"] = reverse("catalogs:ods_oes_list") + f"?tab={self.catalog_key}"
        else:
            ctx["cancel_url"] = reverse(f"catalogs:{stem}_list")
        return ctx

    def dispatch(self, request, *args, **kwargs):
        self.instance = None
        if "pk" in kwargs:
            model = CATALOG_CONFIG[self.catalog_key]["model"]
            self.instance = get_object_or_404(model, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        if not self.instance:
            return {}
        initial = {"code": self.instance.code, "is_active": self.instance.is_active}
        for field in self.get_form_class().base_fields:
            if hasattr(self.instance, field) and field not in initial:
                initial[field] = getattr(self.instance, field)
        return initial

    def form_valid(self, form):
        model = CATALOG_CONFIG[self.catalog_key]["model"]
        fields = _fields_from_form(form, self.catalog_key)
        m2m = None
        try:
            if self.instance:
                update_catalog_record(
                    instance=self.instance,
                    catalog_key=self.catalog_key,
                    actor=self.request.user,
                    request=self.request,
                    code=form.cleaned_data["code"],
                    fields=fields,
                    m2m=m2m,
                )
                messages.success(self.request, "Registro actualizado correctamente.")
            else:
                create_catalog_record(
                    model=model,
                    catalog_key=self.catalog_key,
                    actor=self.request.user,
                    request=self.request,
                    code=form.cleaned_data["code"],
                    fields=fields,
                    m2m=m2m,
                )
                messages.success(self.request, "Registro creado correctamente.")
        except CatalogServiceError as exc:
            if hasattr(exc, "error_dict"):
                for field, errs in exc.error_dict.items():
                    form.add_error(field if field in form.fields else None, errs)
            else:
                form.add_error(None, exc.messages[0])
            return self.form_invalid(form)
        return super().form_valid(form)


class CatalogStateView(SystemAdministratorRequiredMixin, FormView):
    form_class = StateConfirmForm
    template_name = "catalogs/confirm_state.html"

    def dispatch(self, request, catalog_key, pk, *args, **kwargs):
        self.catalog_key = catalog_key
        self.config = CATALOG_CONFIG[catalog_key]
        self.instance = get_object_or_404(self.config["model"], pk=pk)
        self.activate = request.GET.get("action") == "activate"
        return super().dispatch(request, catalog_key, pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["record"] = self.instance
        ctx["config"] = self.config
        ctx["activate"] = self.activate
        return ctx

    def form_valid(self, form):
        self.activate = self.request.POST.get("state_action") == "activate"
        try:
            set_catalog_active_state(
                instance=self.instance,
                catalog_key=self.catalog_key,
                actor=self.request.user,
                request=self.request,
                activate=self.activate,
            )
        except CatalogServiceError as exc:
            form.add_error(None, exc.messages[0])
            return self.form_invalid(form)
        verb = "activado" if self.activate else "desactivado"
        messages.success(self.request, f"Registro {verb} correctamente.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.catalog_key == PROVIDER_KEY:
            return reverse("catalogs:provider_list")
        if self.catalog_key in ("ods", "oes"):
            return reverse("catalogs:ods_oes_list") + f"?tab={self.catalog_key}"
        return reverse(f"catalogs:{self.catalog_key}_list")


class GenericCatalogListView(SystemAdministratorRequiredMixin, View):
    catalog_key: str = ""
    template_name = "catalogs/generic/list.html"
    partial_name = "catalogs/generic/_table.html"

    def get(self, request):
        config = CATALOG_CONFIG[self.catalog_key]
        form = CatalogSearchForm(request.GET)
        q = form.data.get("q", "") if form.is_bound else ""
        status = form.data.get("status", "") if form.is_bound else ""
        queryset = catalog_list_qs(
            config["model"],
            search=q,
            status=status,
            search_fields=config["search_fields"],
        )
        paginator = Paginator(queryset, CATALOG_PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page"))
        stem = _url_stem(self.catalog_key)
        context = {
            "catalog_key": self.catalog_key,
            "url_stem": stem,
            "config": config,
            "form": form,
            "page_obj": page_obj,
            "records": page_obj.object_list,
            "total_count": paginator.count,
            "list_url": reverse(f"catalogs:{stem}_list"),
            "create_url": reverse(f"catalogs:{stem}_create"),
        }
        return _htmx(request, self.partial_name, self.template_name, context)


class ProviderListView(SystemAdministratorRequiredMixin, View):
    template_name = "catalogs/providers/list.html"
    partial_name = "catalogs/providers/_table.html"

    def get(self, request):
        form = ProviderSearchForm(request.GET)
        q = form.data.get("q", "") if form.is_bound else ""
        status = form.data.get("status", "") if form.is_bound else ""
        service_type = form.cleaned_data.get("service_type") if form.is_valid() else None

        def extra(qs):
            if service_type:
                return qs.filter(service_types=service_type).prefetch_related(
                    Prefetch("service_types", queryset=ServiceType.objects.only("name"))
                )
            return qs.prefetch_related("service_types")

        queryset = catalog_list_qs(
            Provider,
            search=q,
            status=status,
            search_fields=("code", "ruc", "legal_name", "main_contact", "email"),
            extra_filter=extra,
        )
        paginator = Paginator(queryset, CATALOG_PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "form": form,
            "page_obj": page_obj,
            "records": page_obj.object_list,
            "total_count": paginator.count,
        }
        return _htmx(request, self.partial_name, self.template_name, context)


class ProviderFormView(SystemAdministratorRequiredMixin, FormView):
    form_class = ProviderForm
    template_name = "catalogs/providers/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.instance = None
        if "pk" in kwargs:
            self.instance = get_object_or_404(Provider, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        if not self.instance:
            return {}
        return {
            "code": self.instance.code,
            "is_active": self.instance.is_active,
            "legal_name": self.instance.legal_name,
            "ruc": self.instance.ruc,
            "phone": self.instance.phone,
            "main_contact": self.instance.main_contact,
            "email": self.instance.email,
            "website": self.instance.website,
            "address": self.instance.address,
            "service_types": self.instance.service_types.all(),
        }

    def form_valid(self, form):
        fields = {
            "is_active": form.cleaned_data.get("is_active", True),
            "legal_name": normalize_name(form.cleaned_data["legal_name"]),
            "ruc": form.cleaned_data["ruc"],
            "phone": form.cleaned_data.get("phone", ""),
            "main_contact": normalize_name(form.cleaned_data["main_contact"]),
            "email": form.cleaned_data["email"],
            "website": form.cleaned_data.get("website", ""),
            "address": normalize_whitespace(form.cleaned_data.get("address", "")),
        }
        m2m = {"service_types": list(form.cleaned_data["service_types"])}
        try:
            exclude_pk = getattr(self.instance, "pk", None)
            if Provider.objects.filter(ruc=fields["ruc"]).exclude(pk=exclude_pk).exists():
                form.add_error("ruc", "Este RUC ya está registrado.")
                return self.form_invalid(form)
            if self.instance:
                update_catalog_record(
                    instance=self.instance,
                    catalog_key=PROVIDER_KEY,
                    actor=self.request.user,
                    request=self.request,
                    code=form.cleaned_data["code"],
                    fields=fields,
                    m2m=m2m,
                )
                messages.success(self.request, "Proveedor actualizado correctamente.")
                return redirect("catalogs:provider_detail", pk=self.instance.pk)
            instance = create_catalog_record(
                model=Provider,
                catalog_key=PROVIDER_KEY,
                actor=self.request.user,
                request=self.request,
                code=form.cleaned_data["code"],
                fields=fields,
                m2m=m2m,
            )
            messages.success(self.request, "Proveedor guardado correctamente.")
            return redirect("catalogs:provider_detail", pk=instance.pk)
        except CatalogServiceError as exc:
            if hasattr(exc, "error_dict"):
                for field, errs in exc.error_dict.items():
                    form.add_error(field if field in form.fields else None, errs)
            else:
                form.add_error(None, exc.messages[0])
            return self.form_invalid(form)


class ProviderDetailView(SystemAdministratorRequiredMixin, TemplateView):
    template_name = "catalogs/providers/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["provider"] = get_object_or_404(
            Provider.objects.prefetch_related("service_types"),
            pk=self.kwargs["pk"],
        )
        return ctx


class ProviderStateView(SystemAdministratorRequiredMixin, FormView):
    form_class = StateConfirmForm
    template_name = "catalogs/confirm_state.html"

    def dispatch(self, request, *args, pk, **kwargs):
        self.instance = get_object_or_404(Provider, pk=pk)
        self.activate = request.GET.get("action") == "activate"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["record"] = self.instance
        ctx["config"] = {"label": "Proveedores", "title": self.instance.legal_name}
        ctx["activate"] = self.activate
        ctx["catalog_key"] = PROVIDER_KEY
        return ctx

    def form_valid(self, form):
        self.activate = self.request.POST.get("state_action") == "activate"
        try:
            set_catalog_active_state(
                instance=self.instance,
                catalog_key=PROVIDER_KEY,
                actor=self.request.user,
                request=self.request,
                activate=self.activate,
            )
        except CatalogServiceError as exc:
            form.add_error(None, exc.messages[0])
            return self.form_invalid(form)
        messages.success(self.request, "Estado del proveedor actualizado.")
        return redirect("catalogs:provider_list")

    def get_success_url(self):
        return reverse("catalogs:provider_list")


# Subclases concretas para URLs de formularios/listas
def _form_view(key):
    class _CreateEdit(GenericCatalogFormView):
        catalog_key = key

    return _CreateEdit


ODSCreateEditView = _form_view("ods")
OESCreateEditView = _form_view("oes")
SiteCreateEditView = _form_view("sedes")
StatusCreateEditView = _form_view("estados")
ServiceTypeCreateEditView = _form_view("tipos-servicio")
DocumentTypeCreateEditView = _form_view("tipos-documentales")
ResponsibleCreateEditView = _form_view("responsables")
