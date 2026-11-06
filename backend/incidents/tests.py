from datetime import datetime, timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

from django.test import TestCase
from openpyxl import load_workbook
from rest_framework.test import APIClient

from api.models import User
from audit.models import AuditEntry
from .models import Incident
from .reports import incident_report_data


class IncidentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {role: User.objects.create_user(
            email=f"{role}@example.com", full_name=f"Personal {role}", role=role,
        ) for role in User.Role.values}

    def setUp(self):
        self.client = APIClient()
        self.guard = self.users[User.Role.GUARDA]
        self.client.force_authenticate(self.guard)

    def incident(self, timestamp, category="objeto_extraviado"):
        incident = Incident.objects.create(user=self.guard, category=category, description="Descripción de prueba de la incidencia.")
        Incident.objects.filter(pk=incident.pk).update(timestamp=timestamp)
        return incident

    def test_list_permissions_and_newest_first_with_staff_name(self):
        start = datetime(2026, 11, 23, 10, tzinfo=ZoneInfo("America/Costa_Rica"))
        first = self.incident(start)
        second = self.incident(start + timedelta(hours=1))
        third = self.incident(start + timedelta(hours=1))
        for role, user in self.users.items():
            self.client.force_authenticate(user)
            with self.subTest(role=role):
                response = self.client.get("/api/incidents/")
                allowed = role in (User.Role.GUARDA, User.Role.ADMINISTRADOR_GENERAL, User.Role.ADMINISTRADOR_SISTEMA)
                self.assertEqual(response.status_code, 200 if allowed else 403)
                if allowed:
                    self.assertEqual(response.json()["count"], 3)
                    self.assertEqual([row["id"] for row in response.json()["results"]], [third.pk, second.pk, first.pk])
                    self.assertEqual(response.json()["results"][0]["user_name"], self.guard.full_name)
                    self.assertNotIn("email", response.json()["results"][0])
                    oldest = self.client.get("/api/incidents/", {"ordering": "timestamp"})
                    self.assertEqual([row["id"] for row in oldest.json()["results"]], [first.pk, second.pk, third.pk])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/incidents/").status_code, 401)

    def test_pagination_keeps_equal_dates_stable_and_reports_complete(self):
        start = datetime(2026, 11, 23, 10, tzinfo=ZoneInfo("America/Costa_Rica"))
        ids = [self.incident(start).pk for _ in range(45)]
        for ordering, expected in (("timestamp", ids), ("-timestamp", list(reversed(ids)))):
            received = []
            for page, size in ((1, 20), (2, 20), (3, 5)):
                with self.subTest(ordering=ordering, page=page):
                    response = self.client.get("/api/incidents/", {"ordering": ordering, "page": page})
                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    self.assertEqual(data["count"], 45)
                    self.assertEqual(len(data["results"]), size)
                    self.assertEqual(bool(data["previous"]), page > 1)
                    self.assertEqual(bool(data["next"]), page < 3)
                    if data["next"]:
                        self.assertIn(f"ordering={ordering}", data["next"])
                    received.extend(row["id"] for row in data["results"])
            self.assertEqual(received, expected)
        oversized = self.client.get("/api/incidents/", {"page_size": 1000})
        self.assertEqual(len(oversized.json()["results"]), 20)

        self.client.force_authenticate(self.users[User.Role.ADMINISTRADOR_SISTEMA])
        filters = {"fecha_inicio": "2026-11-23", "fecha_fin": "2026-11-23"}
        report = self.client.get("/api/reports/consolidated/", filters)
        self.assertEqual(report.json()["incidencias"]["total"], 45)
        response = self.client.get("/api/reports/export/consolidated/xlsx/", filters)
        workbook = load_workbook(BytesIO(response.content), read_only=True)
        sheet = next(name for name in workbook.sheetnames if name.endswith(" - Incidencias"))
        self.assertIn(("Total de incidencias", 45), list(workbook[sheet].values))
        workbook.close()

    def test_empty_pages_and_invalid_query_values(self):
        response = self.client.get("/api/incidents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})
        for value in ("0", "-1", "nope", "999", "1.5"):
            with self.subTest(page=value):
                self.assertEqual(self.client.get("/api/incidents/", {"page": value}).status_code, 404)
        for value in ("id", "category", "-timestamp,pk"):
            with self.subTest(ordering=value):
                response = self.client.get("/api/incidents/", {"ordering": value})
                self.assertEqual(response.status_code, 400)
                self.assertIn("ordering", response.json())

    def test_registration_remains_validated_audited_and_server_owned(self):
        payload = {"category": "otro", "description": " Incidencia registrada desde la pantalla. "}
        for field in ("user", "user_name", "timestamp", "status"):
            with self.subTest(field=field):
                self.assertEqual(self.client.post("/api/incidents/", {**payload, field: "spoofed"}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/incidents/", {**payload, "description": "Corta"}, format="json").status_code, 400)
        response = self.client.post("/api/incidents/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"], self.guard.pk)
        self.assertEqual(response.json()["user_name"], self.guard.full_name)
        self.assertEqual(Incident.objects.count(), 1)
        self.assertEqual(AuditEntry.objects.filter(entity="incident", action_type="create").count(), 1)
        self.assertEqual(self.client.patch("/api/incidents/", payload, format="json").status_code, 405)

    def test_reports_use_inclusive_local_dates_and_export_incident_only_data(self):
        start = datetime(2026, 11, 23, tzinfo=ZoneInfo("America/Costa_Rica"))
        self.incident(start - timedelta(seconds=1))
        self.incident(start)
        self.incident(start + timedelta(days=1, seconds=-1), "dano_infraestructura")
        self.incident(start + timedelta(days=1), "comportamiento_indebido")
        expected = {"total": 2, "por_categoria": {category: 0 for category in Incident.Category.values}}
        expected["por_categoria"].update(objeto_extraviado=1, dano_infraestructura=1)
        self.assertEqual(incident_report_data(start.date(), start.date()), expected)
        self.assertEqual(incident_report_data(start.date(), None)["total"], 3)
        self.assertEqual(incident_report_data(None, start.date())["total"], 3)
        self.assertEqual(incident_report_data()["total"], 4)

        filters = {"fecha_inicio": "2026-11-23", "fecha_fin": "2026-11-23"}
        for role in (User.Role.ADMINISTRADOR_GENERAL, User.Role.ADMINISTRADOR_SISTEMA):
            self.client.force_authenticate(self.users[role])
            report = self.client.get("/api/reports/consolidated/", filters)
            self.assertEqual(report.status_code, 200)
            self.assertEqual(report.json()["incidencias"], expected)
            for extension in ("pdf", "xlsx"):
                response = self.client.get(f"/api/reports/export/consolidated/{extension}/", filters)
                self.assertEqual(response.status_code, 200)
                if extension == "xlsx":
                    workbook = load_workbook(BytesIO(response.content), read_only=True)
                    sheet = next(name for name in workbook.sheetnames if name.endswith(" - Incidencias"))
                    rows = list(workbook[sheet].values)
                    self.assertIn(("Total de incidencias", 2), rows)
                    self.assertIn(("Objeto extraviado", 1), rows)
                    self.assertIn(("Daño a infraestructura", 1), rows)
                    workbook.close()
                else:
                    self.assertTrue(response.content.startswith(b"%PDF"))
            empty = {"fecha_inicio": "2026-12-01", "fecha_fin": "2026-12-01"}
            report = self.client.get("/api/reports/consolidated/", empty)
            self.assertEqual(report.json()["incidencias"]["total"], 0)
            self.assertTrue(all(value == 0 for value in report.json()["incidencias"]["por_categoria"].values()))
            self.assertEqual(self.client.get("/api/reports/export/consolidated/pdf/", empty).status_code, 400)
