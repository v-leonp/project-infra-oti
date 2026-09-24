from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.administration.constants import ROLE_ADMINISTRADOR, ROLE_USUARIO
from apps.administration.models import AuditLog
from apps.administration.role_setup import ensure_system_groups, setup_roles_and_permissions
from apps.catalogs.models import ODS, Provider, Responsible, Site
from apps.internet.constants import (
    SERVICE_STATUS_ACTIVE,
    SERVICE_STATUS_EXPIRED,
    SERVICE_STATUS_EXPIRING,
)
from apps.internet.models import InternetService, ServiceIncident
from apps.internet.state import compute_service_status, expiry_warning_days

User = get_user_model()


@pytest.fixture
def roles(db):
    setup_roles_and_permissions()
    return ensure_system_groups()


@pytest.fixture
def admin_user(db, roles):
    user = User.objects.create_user("admin.int", "admin@int.local", "AdminInt123!")
    user.groups.add(roles[ROLE_ADMINISTRADOR])
    return user


@pytest.fixture
def regular_user(db, roles):
    user = User.objects.create_user(
        "usuario.int",
        "user@int.local",
        "UserInt123!",
        first_name="Usuario",
        last_name="Operativo",
    )
    user.groups.add(roles[ROLE_USUARIO])
    return user


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser("super.int", "super@int.local", "SuperInt123!")


@pytest.fixture
def user_client(regular_user):
    client = Client()
    client.login(username="usuario.int", password="UserInt123!")
    return client


@pytest.fixture
def admin_client(admin_user):
    client = Client()
    client.login(username="admin.int", password="AdminInt123!")
    return client


@pytest.fixture
def catalog_bundle(db, admin_user):
    ods = ODS.objects.create(
        code="ODS-01",
        name="Demo",
        description="",
        created_by=admin_user,
        updated_by=admin_user,
    )
    site = Site.objects.create(
        code="SED-01",
        name="Sede Central",
        created_by=admin_user,
        updated_by=admin_user,
    )
    provider = Provider.objects.create(
        code="PROV-01",
        legal_name="Tecnored",
        ruc="20123456789",
        main_contact="Ana",
        email="ana@demo.local",
        created_by=admin_user,
        updated_by=admin_user,
    )
    responsible = Responsible.objects.create(
        code="RES-01",
        first_name="Juan",
        last_name="Martínez",
        job_title="TI",
        email="juan@demo.local",
        site=site,
        created_by=admin_user,
        updated_by=admin_user,
    )
    return {"ods": ods, "site": site, "provider": provider, "responsible": responsible}


def _service_payload(catalog_bundle, **overrides):
    today = timezone.localdate()
    data = {
        "code": "INT-001",
        "ods_oes_type": "ods",
        "ods": catalog_bundle["ods"].pk,
        "oes": "",
        "site": catalog_bundle["site"].pk,
        "provider": catalog_bundle["provider"].pk,
        "responsible": catalog_bundle["responsible"].pk,
        "link_type": "fibra_optica",
        "contracted_speed": "200",
        "speed_unit": "Mbps",
        "public_ip": "189.203.10.45",
        "circuit_id": "CKT-1",
        "connection_medium": "Fibra",
        "technical_observations": "",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=120)).isoformat(),
        "observations": "Observación demo",
        "marked_with_observations": False,
        "is_active": True,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestInternetAccess:
    def test_user_can_access_services(self, user_client):
        assert user_client.get(reverse("internet:service_list")).status_code == 200

    def test_admin_forbidden(self, admin_client):
        assert admin_client.get(reverse("internet:service_list")).status_code == 403

    def test_superuser_forbidden(self, superuser):
        client = Client()
        client.login(username="super.int", password="SuperInt123!")
        assert client.get(reverse("internet:service_list")).status_code == 403

    def test_menu_visible_only_for_user(self, user_client, admin_client):
        assert "Servicios" in user_client.get(reverse("accounts:welcome")).content.decode()
        assert "Servicios" not in admin_client.get(reverse("accounts:welcome")).content.decode()

    def test_htmx_forbidden_for_admin(self, admin_client):
        response = admin_client.get(
            reverse("internet:service_list"),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestInternetServices:
    def test_create_service(self, user_client, catalog_bundle):
        response = user_client.post(
            reverse("internet:service_create"),
            data=_service_payload(catalog_bundle),
        )
        assert response.status_code == 302
        assert InternetService.objects.filter(code="INT-001").exists()
        assert AuditLog.objects.filter(action="internet_service_created").exists()

    def test_duplicate_code_rejected(self, user_client, catalog_bundle, regular_user):
        InternetService.objects.create(
            code="INT-DUP",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=100,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            created_by=regular_user,
            updated_by=regular_user,
        )
        response = user_client.post(
            reverse("internet:service_create"),
            data=_service_payload(catalog_bundle, code="int-dup"),
        )
        assert response.status_code == 200
        assert "código" in response.content.decode().lower()

    def test_date_validation(self, user_client, catalog_bundle):
        today = timezone.localdate()
        response = user_client.post(
            reverse("internet:service_create"),
            data=_service_payload(
                catalog_bundle,
                start_date=today.isoformat(),
                end_date=(today - timedelta(days=1)).isoformat(),
            ),
        )
        assert response.status_code == 200
        assert "término" in response.content.decode().lower()

    def test_invalid_ip_rejected(self, user_client, catalog_bundle):
        response = user_client.post(
            reverse("internet:service_create"),
            data=_service_payload(catalog_bundle, public_ip="not-an-ip"),
        )
        assert response.status_code == 200

    def test_speed_must_be_positive(self, user_client, catalog_bundle):
        response = user_client.post(
            reverse("internet:service_create"),
            data=_service_payload(catalog_bundle, contracted_speed="0"),
        )
        assert response.status_code == 200

    def test_kpis_from_database(self, user_client, catalog_bundle, regular_user):
        today = timezone.localdate()
        InternetService.objects.create(
            code="INT-A",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=100,
            start_date=today,
            end_date=today + timedelta(days=expiry_warning_days() + 10),
            created_by=regular_user,
            updated_by=regular_user,
        )
        InternetService.objects.create(
            code="INT-B",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=50,
            start_date=today,
            end_date=today + timedelta(days=5),
            created_by=regular_user,
            updated_by=regular_user,
        )
        html = user_client.get(reverse("internet:service_list")).content.decode()
        assert "INT-A" in html
        assert html.count("text-3xl font-bold") >= 1

    def test_status_computation(self):
        today = date(2025, 6, 1)
        assert (
            compute_service_status(
                is_active=True,
                end_date=today + timedelta(days=60),
                marked_with_observations=False,
                on_date=today,
            )
            == SERVICE_STATUS_ACTIVE
        )
        assert (
            compute_service_status(
                is_active=True,
                end_date=today + timedelta(days=10),
                marked_with_observations=False,
                on_date=today,
            )
            == SERVICE_STATUS_EXPIRING
        )
        assert (
            compute_service_status(
                is_active=True,
                end_date=today - timedelta(days=1),
                marked_with_observations=False,
                on_date=today,
            )
            == SERVICE_STATUS_EXPIRED
        )

    def test_filter_search(self, user_client, catalog_bundle, regular_user):
        InternetService.objects.create(
            code="INT-SEARCH",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=10,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=40),
            created_by=regular_user,
            updated_by=regular_user,
        )
        response = user_client.get(reverse("internet:service_list"), {"q": "INT-SEARCH"})
        assert response.status_code == 200
        assert "INT-SEARCH" in response.content.decode()

    def test_list_queries_bounded(self, user_client, catalog_bundle, regular_user):
        today = timezone.localdate()
        for i in range(3):
            InternetService.objects.create(
                code=f"INT-Q{i}",
                ods=catalog_bundle["ods"],
                site=catalog_bundle["site"],
                provider=catalog_bundle["provider"],
                link_type="fibra_optica",
                contracted_speed=10,
                start_date=today,
                end_date=today + timedelta(days=90),
                created_by=regular_user,
                updated_by=regular_user,
            )
        with CaptureQueriesContext(connection) as ctx:
            user_client.get(reverse("internet:service_list"))
        assert len(ctx.captured_queries) <= 25

    def test_post_only_state_change(self, user_client, catalog_bundle, regular_user):
        service = InternetService.objects.create(
            code="INT-ST",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=10,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=90),
            created_by=regular_user,
            updated_by=regular_user,
        )
        assert user_client.get(reverse("internet:service_state", kwargs={"pk": service.pk})).status_code == 200
        assert (
            user_client.post(
                reverse("internet:service_state", kwargs={"pk": service.pk}),
                data={"is_active": "on", "marked_with_observations": "on", "reason": "Revisión"},
            ).status_code
            == 302
        )


@pytest.mark.django_db
class TestInternetContractsDeliverablesIncidents:
    def test_create_contract(self, user_client, catalog_bundle, regular_user):
        service = InternetService.objects.create(
            code="INT-C",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=10,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=90),
            created_by=regular_user,
            updated_by=regular_user,
        )
        today = timezone.localdate()
        response = user_client.post(
            reverse("internet:contract_create"),
            data={
                "contract_number": "CONT-2025-01",
                "service": service.pk,
                "provider": catalog_bundle["provider"].pk,
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=90)).isoformat(),
                "status": "active",
                "observations": "",
            },
        )
        assert response.status_code == 302

    def test_deliverable_timeliness(self, user_client, catalog_bundle, regular_user):
        service = InternetService.objects.create(
            code="INT-E",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=10,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=90),
            created_by=regular_user,
            updated_by=regular_user,
        )
        due = timezone.localdate() + timedelta(days=5)
        submitted = timezone.now() - timedelta(days=1)
        response = user_client.post(
            reverse("internet:deliverable_create"),
            data={
                "service": service.pk,
                "contract": "",
                "period": "2025-Q1",
                "name": "Informe mensual",
                "due_date": due.isoformat(),
                "submitted_at": submitted.strftime("%Y-%m-%dT%H:%M"),
                "status": "submitted",
                "observations": "",
            },
        )
        assert response.status_code == 302

    def test_incident_duration(self, user_client, catalog_bundle, regular_user):
        service = InternetService.objects.create(
            code="INT-I",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=10,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=90),
            created_by=regular_user,
            updated_by=regular_user,
        )
        start = timezone.now() - timedelta(hours=2)
        end = timezone.now()
        response = user_client.post(
            reverse("internet:incident_create"),
            data={
                "ticket_code": "INC-001",
                "service": service.pk,
                "started_at": start.strftime("%Y-%m-%dT%H:%M"),
                "ended_at": end.strftime("%Y-%m-%dT%H:%M"),
                "description": "Corte de enlace",
                "cause": "Fibra",
                "action_taken": "Reparación",
                "responsible": catalog_bundle["responsible"].pk,
                "attribution": "",
                "observations": "",
            },
        )
        assert response.status_code == 302
        incident = ServiceIncident.objects.get(ticket_code="INC-001")
        assert incident.downtime_minutes is not None
        assert incident.downtime_minutes >= 110


@pytest.mark.django_db
class TestInternetDocuments:
    def test_reject_executable(self, user_client, catalog_bundle, admin_user, regular_user):
        from apps.catalogs.models import DocumentType

        doc_type = DocumentType.objects.create(
            code="TD-01",
            name="Contrato",
            created_by=admin_user,
            updated_by=admin_user,
        )
        service = InternetService.objects.create(
            code="INT-DOC",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=10,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=90),
            created_by=regular_user,
            updated_by=regular_user,
        )
        bad = SimpleUploadedFile("malware.exe", b"MZ", content_type="application/octet-stream")
        response = user_client.post(
            reverse("internet:document_list"),
            data={
                "name": "Malicioso",
                "document_type": doc_type.pk,
                "related_type": "service",
                "service": service.pk,
                "document_date": timezone.localdate().isoformat(),
                "description": "",
                "file": bad,
            },
        )
        assert response.status_code == 200

    def test_download_requires_auth(self, catalog_bundle, regular_user, admin_user):
        from apps.catalogs.models import DocumentType
        from apps.internet.models import ServiceDocument

        doc_type = DocumentType.objects.create(
            code="TD-02",
            name="Anexo",
            created_by=admin_user,
            updated_by=admin_user,
        )
        service = InternetService.objects.create(
            code="INT-DL",
            ods=catalog_bundle["ods"],
            site=catalog_bundle["site"],
            provider=catalog_bundle["provider"],
            link_type="fibra_optica",
            contracted_speed=10,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=90),
            created_by=regular_user,
            updated_by=regular_user,
        )
        upload = SimpleUploadedFile("doc.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        doc = ServiceDocument.objects.create(
            name="Prueba",
            document_type=doc_type,
            related_type="service",
            service=service,
            document_date=timezone.localdate(),
            file=upload,
            original_filename="doc.pdf",
            uploaded_by=regular_user,
        )
        anon = Client()
        assert anon.get(reverse("internet:document_download", kwargs={"pk": doc.pk})).status_code == 302
        client = Client()
        client.login(username="usuario.int", password="UserInt123!")
        assert client.get(reverse("internet:document_download", kwargs={"pk": doc.pk})).status_code == 200

    def test_csrf_required_on_create(self, user_client, catalog_bundle):
        client = Client(enforce_csrf_checks=True)
        client.login(username="usuario.int", password="UserInt123!")
        response = client.post(
            reverse("internet:service_create"),
            data=_service_payload(catalog_bundle),
        )
        assert response.status_code == 403
