import csv
from io import StringIO

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.internet.constants import (
    AUDIT_DOCUMENT_DOWNLOADED,
    INTERNET_PAGE_SIZE,
    SERVICE_STATUS_ACTIVE,
    SERVICE_STATUS_EXPIRED,
    SERVICE_STATUS_EXPIRING,
    SERVICE_STATUS_OBSERVATIONS,
)
from apps.internet.forms import (
    InternetServiceForm,
    ReportFilterForm,
    ServiceContractForm,
    ServiceDeliverableForm,
    ServiceDocumentForm,
    ServiceIncidentForm,
    ServiceSearchForm,
    ServiceStateForm,
)
from apps.internet.mixins import InternetModuleUserRequiredMixin
from apps.internet.models import (
    InternetService,
    ServiceContract,
    ServiceDeliverable,
    ServiceDocument,
    ServiceIncident,
)
from apps.internet.selectors import (
    contracts_qs,
    deliverables_qs,
    documents_qs,
    filter_services,
    incidents_qs,
    report_services_qs,
    service_kpis,
)
from apps.internet.services import (
    create_contract,
    create_deliverable,
    create_incident,
    create_service,
    create_service_document,
    update_contract,
    update_deliverable,
    update_incident,
    update_service,
    update_service_state,
)
from apps.internet.services.audit import log_internet_event


def _htmx(request, partial, full, context):
    if request.headers.get("HX-Request"):
        return render(request, partial, context)
    return render(request, full, context)


def _filter_params(form: ServiceSearchForm) -> dict:
    if not form.is_valid():
        return {"order": "code"}
    return {
        "search": form.cleaned_data.get("q", ""),
        "site_id": str(form.cleaned_data.get("site") or "") or None,
        "provider_id": str(form.cleaned_data.get("provider") or "") or None,
        "status": form.cleaned_data.get("status", ""),
        "ods_id": str(form.cleaned_data.get("ods") or "") or None,
        "oes_id": str(form.cleaned_data.get("oes") or "") or None,
        "validity": form.cleaned_data.get("validity", ""),
        "order": form.cleaned_data.get("order") or "code",
    }


class ServiceListView(InternetModuleUserRequiredMixin, View):
    template_name = "internet/services/list.html"
    partial_name = "internet/services/_table.html"

    def get(self, request):
        form = ServiceSearchForm(request.GET)
        form.is_valid()
        params = _filter_params(form)
        queryset = filter_services(**params)
        paginator = Paginator(queryset, INTERNET_PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "form": form,
            "page_obj": page_obj,
            "records": page_obj.object_list,
            "total_count": paginator.count,
            "kpis": service_kpis(),
            "list_url": reverse("internet:service_list"),
        }
        return _htmx(request, self.partial_name, self.template_name, context)


class ServiceDetailView(InternetModuleUserRequiredMixin, TemplateView):
    template_name = "internet/services/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = get_object_or_404(
            InternetService.objects.select_related("ods", "oes", "site", "provider", "responsible"),
            pk=self.kwargs["pk"],
        )
        ctx["service"] = service
        ctx["contracts"] = service.contracts.filter(is_active=True)[:10]
        ctx["incidents"] = service.incidents.filter(is_active=True)[:10]
        return ctx


class ServiceCreateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/services/form.html"
    form_class = InternetServiceForm

    def form_valid(self, form):
        try:
            create_service(self.request, self.request.user, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Servicio registrado correctamente.")
        return redirect("internet:service_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_create"] = True
        return ctx


class ServiceUpdateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/services/form.html"
    form_class = InternetServiceForm

    def dispatch(self, request, *args, **kwargs):
        self.instance = get_object_or_404(InternetService, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        try:
            update_service(self.request, self.request.user, self.instance, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Servicio actualizado correctamente.")
        return redirect("internet:service_detail", pk=self.instance.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_create"] = False
        ctx["service"] = self.instance
        return ctx


class ServiceStateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/services/state.html"
    form_class = ServiceStateForm

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(InternetService, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            "is_active": self.service.is_active,
            "marked_with_observations": self.service.marked_with_observations,
        }

    def form_valid(self, form):
        update_service_state(
            self.request,
            self.request.user,
            self.service,
            is_active=form.cleaned_data.get("is_active"),
            marked_with_observations=form.cleaned_data.get("marked_with_observations"),
            reason=form.cleaned_data.get("reason", ""),
        )
        messages.success(self.request, "Estado del servicio actualizado.")
        return redirect("internet:service_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["service"] = self.service
        return ctx


class ContractListView(InternetModuleUserRequiredMixin, TemplateView):
    template_name = "internet/contracts/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paginator = Paginator(contracts_qs(), INTERNET_PAGE_SIZE)
        ctx["page_obj"] = paginator.get_page(self.request.GET.get("page"))
        ctx["records"] = ctx["page_obj"].object_list
        ctx["total_count"] = paginator.count
        return ctx


class ContractCreateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/contracts/form.html"
    form_class = ServiceContractForm

    def form_valid(self, form):
        try:
            create_contract(self.request, self.request.user, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Contrato registrado.")
        return redirect("internet:contract_list")


class ContractUpdateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/contracts/form.html"
    form_class = ServiceContractForm

    def dispatch(self, request, *args, **kwargs):
        self.instance = get_object_or_404(ServiceContract, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        try:
            update_contract(self.request, self.request.user, self.instance, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Contrato actualizado.")
        return redirect("internet:contract_list")


class DeliverableListView(InternetModuleUserRequiredMixin, TemplateView):
    template_name = "internet/deliverables/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paginator = Paginator(deliverables_qs(), INTERNET_PAGE_SIZE)
        ctx["page_obj"] = paginator.get_page(self.request.GET.get("page"))
        ctx["records"] = ctx["page_obj"].object_list
        ctx["total_count"] = paginator.count
        return ctx


class DeliverableCreateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/deliverables/form.html"
    form_class = ServiceDeliverableForm

    def form_valid(self, form):
        create_deliverable(self.request, self.request.user, form.cleaned_data)
        messages.success(self.request, "Entregable registrado.")
        return redirect("internet:deliverable_list")


class DeliverableUpdateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/deliverables/form.html"
    form_class = ServiceDeliverableForm

    def dispatch(self, request, *args, **kwargs):
        self.instance = get_object_or_404(ServiceDeliverable, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        update_deliverable(self.request, self.request.user, self.instance, form.cleaned_data)
        messages.success(self.request, "Entregable actualizado.")
        return redirect("internet:deliverable_list")


class IncidentListView(InternetModuleUserRequiredMixin, TemplateView):
    template_name = "internet/incidents/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paginator = Paginator(incidents_qs(), INTERNET_PAGE_SIZE)
        ctx["page_obj"] = paginator.get_page(self.request.GET.get("page"))
        ctx["records"] = ctx["page_obj"].object_list
        ctx["total_count"] = paginator.count
        return ctx


class IncidentCreateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/incidents/form.html"
    form_class = ServiceIncidentForm

    def form_valid(self, form):
        try:
            create_incident(self.request, self.request.user, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Incidencia registrada.")
        return redirect("internet:incident_list")


class IncidentUpdateView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/incidents/form.html"
    form_class = ServiceIncidentForm

    def dispatch(self, request, *args, **kwargs):
        self.instance = get_object_or_404(ServiceIncident, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        try:
            update_incident(self.request, self.request.user, self.instance, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Incidencia actualizada.")
        return redirect("internet:incident_list")


class DocumentListView(InternetModuleUserRequiredMixin, FormView):
    template_name = "internet/documents/list.html"
    form_class = ServiceDocumentForm

    def get(self, request, *args, **kwargs):
        paginator = Paginator(documents_qs(), INTERNET_PAGE_SIZE)
        return render(
            request,
            self.template_name,
            {
                "form": self.form_class(),
                "page_obj": paginator.get_page(request.GET.get("page")),
                "records": paginator.get_page(request.GET.get("page")).object_list,
                "total_count": paginator.count,
            },
        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            try:
                cleaned = form.cleaned_data
                create_service_document(
                    request,
                    request.user,
                    name=cleaned["name"],
                    document_type=cleaned["document_type"],
                    related_type=cleaned["related_type"],
                    document_date=cleaned["document_date"],
                    description=cleaned.get("description", ""),
                    uploaded_file=cleaned["file"],
                    service=cleaned.get("service"),
                    contract=cleaned.get("contract"),
                    deliverable=cleaned.get("deliverable"),
                    incident=cleaned.get("incident"),
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, "Documento cargado correctamente.")
                return redirect("internet:document_list")
        paginator = Paginator(documents_qs(), INTERNET_PAGE_SIZE)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "page_obj": paginator.get_page(1),
                "records": paginator.page(1).object_list,
                "total_count": paginator.count,
            },
        )


class DocumentDownloadView(InternetModuleUserRequiredMixin, View):
    def get(self, request, pk):
        doc = get_object_or_404(ServiceDocument, pk=pk)
        if not doc.file:
            raise Http404
        log_internet_event(
            request=request,
            actor=request.user,
            action=AUDIT_DOCUMENT_DOWNLOADED,
            record_type="document",
            record_id=doc.pk,
            new_values={"name": doc.name},
        )
        return FileResponse(doc.file.open("rb"), as_attachment=True, filename=doc.original_filename or doc.name)


class ReportView(InternetModuleUserRequiredMixin, View):
    template_name = "internet/reports/index.html"
    print_template = "internet/reports/print.html"

    def get(self, request):
        form = ReportFilterForm(request.GET)
        results = []
        report_type = request.GET.get("report_type", "active")
        if form.is_valid():
            report_type = form.cleaned_data.get("report_type") or report_type
            filters = {
                "q": form.cleaned_data.get("q", ""),
                "site": str(form.cleaned_data.get("site") or ""),
                "provider": str(form.cleaned_data.get("provider") or ""),
                "ods": str(form.cleaned_data.get("ods") or ""),
                "oes": str(form.cleaned_data.get("oes") or ""),
                "status": form.cleaned_data.get("status", ""),
                "validity": form.cleaned_data.get("validity", ""),
            }
            if report_type in ("active", "expiring", "expired", "observations"):
                status_map = {
                    "active": SERVICE_STATUS_ACTIVE,
                    "expiring": SERVICE_STATUS_EXPIRING,
                    "expired": SERVICE_STATUS_EXPIRED,
                    "observations": SERVICE_STATUS_OBSERVATIONS,
                }
                filters["status"] = status_map[report_type]
                results = list(report_services_qs(filters)[:500])
            elif report_type == "incidents":
                results = list(incidents_qs()[:500])
            elif report_type == "deliverables":
                results = list(deliverables_qs()[:500])
        if request.GET.get("export") == "csv":
            return self._csv_export(report_type, results)
        if request.GET.get("print") == "1":
            return render(
                request,
                self.print_template,
                {"form": form, "results": results, "report_type": report_type},
            )
        return render(
            request,
            self.template_name,
            {"form": form, "results": results, "report_type": report_type},
        )

    def _csv_export(self, report_type, results):
        buffer = StringIO()
        writer = csv.writer(buffer)
        if report_type in ("incidents",):
            writer.writerow(["Ticket", "Servicio", "Inicio", "Estado", "Duración (min)"])
            for row in results:
                writer.writerow(
                    [
                        row.ticket_code,
                        row.service.code,
                        row.started_at,
                        row.status,
                        row.downtime_minutes or "",
                    ]
                )
        elif report_type == "deliverables":
            writer.writerow(["Servicio", "Periodo", "Nombre", "Límite", "Estado", "A tiempo"])
            for row in results:
                writer.writerow(
                    [
                        row.service.code,
                        row.period,
                        row.name,
                        row.due_date,
                        row.status,
                        row.submitted_on_time,
                    ]
                )
        else:
            writer.writerow(["Código", "ODS/OES", "Sede", "Proveedor", "Vigencia", "Estado"])
            for row in results:
                writer.writerow(
                    [
                        row.code,
                        row.ods_oes_label,
                        row.site.name,
                        row.provider.legal_name,
                        row.end_date,
                        row.display_status,
                    ]
                )
        response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="reporte-{report_type}.csv"'
        return response
