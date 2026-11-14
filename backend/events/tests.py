from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from audit.models import AuditEntry
from .models import Evento


class EventTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coordinator = User.objects.create_user(
            email="coordinator@example.com", full_name="Coordinator",
            role=User.Role.COORDINADOR,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.coordinator)
        self.data = {
            "fecha": (timezone.now() + timedelta(days=3)).isoformat(),
            "descripcion": "Museum tour", "ubicacion": "Main hall",
            "tipo": "publico", "asistentes_esperados": 20,
        }

    def test_create_edit_and_cancel_preserve_audit_history(self):
        response = self.client.post("/api/events/", self.data, format="json")
        self.assertEqual(response.status_code, 201)
        event_id = response.json()["id"]
        path = f"/api/events/{event_id}/"
        self.assertEqual(self.client.patch(path, {"descripcion": "Updated tour"}, format="json").status_code, 200)
        self.assertEqual(self.client.post(path + "cancel/", {}, format="json").status_code, 400)
        self.assertEqual(self.client.post(path + "cancel/", {"confirm": True}, format="json").status_code, 200)
        event = Evento.objects.get(pk=event_id)
        self.assertEqual(event.estado, Evento.Estado.CANCELADO)
        self.assertEqual(AuditEntry.objects.filter(entity="evento", entity_id=str(event_id)).count(), 3)

    def test_public_list_excludes_private_and_cancelled_events(self):
        for kind, state in [("publico", "programado"), ("privado", "programado"), ("publico", "cancelado")]:
            Evento.objects.create(**{**self.data, "tipo": kind, "estado": state}, creado_por=self.coordinator)
        self.client.force_authenticate(None)
        events = self.client.get("/api/events/").json()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tipo"], "publico")
        self.assertNotIn("asistentes_esperados", events[0])

    def test_attendance_requires_past_event_and_integer(self):
        event = Evento.objects.create(**self.data, creado_por=self.coordinator)
        path = f"/api/events/{event.pk}/attendance/"
        self.assertEqual(self.client.patch(path, {"asistentes_reales": 12}, format="json").status_code, 400)
        event.fecha = timezone.now() - timedelta(days=1)
        event.save()
        for value in [True, "12", -1, 1.5]:
            with self.subTest(value=value):
                self.assertEqual(self.client.patch(path, {"asistentes_reales": value}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(path, {"asistentes_reales": 12}, format="json").status_code, 200)
        report = self.client.get("/api/reports/attendance/")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.json()["totales"]["asistentes_reales"], 12)

    def test_attendance_report_remains_coordinator_only(self):
        for role in User.Role:
            user = User.objects.create_user(email=f"{role}@example.com", full_name=role, role=role)
            self.client.force_authenticate(user)
            with self.subTest(role=role):
                self.assertEqual(self.client.get("/api/reports/attendance/").status_code, 200 if role == User.Role.COORDINADOR else 403)
