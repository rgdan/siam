from contextlib import redirect_stdout
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import patch

from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from audit.models import AuditEntry
from collection_integrity.models import Photo, Piece
from cargar_datos_demo import INICIO_DEMO, cargar_datos_demo
from incidents.models import Incident
from system_configuration.models import Parameter
from visitors.models import VisitorEntry

from .models import Evento, User


class DemoDataTests(TestCase):
    def seed(self):
        with redirect_stdout(StringIO()):
            cargar_datos_demo()

    def test_scenario_covers_models_states_dates_and_report_exports(self):
        now = INICIO_DEMO + timedelta(days=2, hours=9)
        with patch("django.utils.timezone.now", return_value=now):
            self.seed()
            self.assertEqual(User.objects.count(), 5)
            self.assertEqual(Piece.objects.count(), 9)
            self.assertEqual(Photo.objects.count(), 18)
            self.assertEqual(Evento.objects.count(), 15)
            self.assertEqual(VisitorEntry.objects.count(), 134)
            self.assertEqual(Incident.objects.count(), 5)
            self.assertEqual(Parameter.objects.count(), 5)
            self.assertEqual(set(Piece.objects.values_list("state", flat=True)),
                             {"stored", "displayed", "loaned", "lost", "stolen", "decommissioned"})
            self.assertEqual(set(Incident.objects.values_list("category", flat=True)), set(Incident.Category.values))
            self.assertTrue(Piece.objects.filter(collection="").exists())
            self.assertTrue(Evento.objects.filter(estado="cancelado").exists())
            self.assertEqual(VisitorEntry.objects.filter(timestamp__date__range=("2026-11-23", "2026-11-29")).count(), 134)
            self.assertEqual(VisitorEntry.objects.values("age_group", "nationality", "sex").distinct().count(), 8)
            self.assertFalse(Evento.objects.filter(fecha__gt=now, asistentes_reales__isnull=False).exists())
            self.assertTrue(Evento.objects.filter(fecha__lt=now, asistentes_reales=0).exists())
            for model in (User, Piece, Photo, Evento, VisitorEntry, Incident, Parameter):
                for record in model.objects.all():
                    record.full_clean()
            for photo in Photo.objects.all():
                with Image.open(BytesIO(photo.content)) as image:
                    image.verify()
            self.assertEqual(set(AuditEntry.objects.values_list("entity", flat=True)),
                             {"user", "piece", "evento", "visitor_entry", "incident", "system_parameter"})

            client = APIClient()
            client.force_authenticate(User.objects.get(role=User.Role.COORDINADOR))
            report = client.get("/api/reports/attendance/", {"fecha_inicio": "2026-11-23", "fecha_fin": "2026-11-29"})
            self.assertEqual(report.status_code, 200)
            self.assertGreater(report.json()["totales"]["asistentes_reales"], 0)
            client.force_authenticate(User.objects.get(role=User.Role.ADMINISTRADOR_SISTEMA))
            filters = {"fecha_inicio": "2026-11-23", "fecha_fin": "2026-11-29"}
            report = client.get("/api/reports/consolidated/", filters)
            self.assertEqual(report.status_code, 200)
            self.assertEqual(report.json()["visitantes"]["total"], 134)
            self.assertEqual(report.json()["colecciones"]["total"], 9)
            for kind in ("consolidated", "attendance"):
                for extension in ("pdf", "xlsx"):
                    with self.subTest(kind=kind, extension=extension):
                        response = client.get(f"/api/reports/export/{kind}/{extension}/", filters)
                        self.assertEqual(response.status_code, 200)
                        self.assertTrue(response.content.startswith(b"%PDF" if extension == "pdf" else b"PK"))

    def test_rerun_preserves_counts_and_user_changes(self):
        self.seed()
        models = (User, Piece, Photo, Evento, VisitorEntry, Incident, Parameter, AuditEntry)
        before = {model: model.objects.count() for model in models}
        user = User.objects.get(role=User.Role.GUARDA)
        user.full_name = "Cuenta personalizada"
        user.set_password("Local-Changed-123")
        user.save()
        piece = Piece.objects.first()
        piece.title = "Título actualizado"
        piece.save()
        event = Evento.objects.first()
        event.ubicacion = "Sala actualizada"
        event.descripcion = "Evento actualizado por el coordinador"
        event.fecha += timedelta(days=1)
        updated_date = event.fecha
        event.save()
        parameter = Parameter.objects.get(key="museum_name")
        parameter.value = "Nombre personalizado"
        parameter.save()
        self.seed()
        self.assertEqual({model: model.objects.count() for model in models}, before)
        user.refresh_from_db()
        piece.refresh_from_db()
        event.refresh_from_db()
        parameter.refresh_from_db()
        self.assertEqual(user.full_name, "Cuenta personalizada")
        self.assertTrue(user.check_password("Local-Changed-123"))
        self.assertEqual(piece.title, "Título actualizado")
        self.assertEqual(event.ubicacion, "Sala actualizada")
        self.assertEqual(event.descripcion, "Evento actualizado por el coordinador")
        self.assertEqual(event.fecha, updated_date)
        self.assertEqual(parameter.value, "Nombre personalizado")

    def test_failure_rolls_back_the_entire_load(self):
        with patch("collection_integrity.services.register_piece", side_effect=RuntimeError("seed failed")):
            with self.assertRaisesRegex(RuntimeError, "seed failed"):
                self.seed()
        for model in (User, Parameter, Piece, Photo, Evento, VisitorEntry, Incident, AuditEntry):
            self.assertEqual(model.objects.count(), 0)
