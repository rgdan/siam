from django.test import TestCase
from rest_framework.test import APIClient

from collection_integrity.models import Piece

from .models import User


class ConsolidatedReportAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Piece.objects.create(title="Report fixture")

    def test_report_and_exports_require_an_administrator(self):
        paths = [
            "/api/reports/consolidated/",
            "/api/reports/export/consolidated/pdf/",
            "/api/reports/export/consolidated/xlsx/",
        ]
        client = APIClient()
        for role in User.Role:
            user = User.objects.create_user(
                email=f"{role}@example.com", full_name=role, role=role,
            )
            client.force_authenticate(user=user)
            expected = 200 if role in (
                User.Role.ADMINISTRADOR_GENERAL,
                User.Role.ADMINISTRADOR_SISTEMA,
            ) else 403
            for path in paths:
                with self.subTest(role=role, path=path):
                    self.assertEqual(client.get(path).status_code, expected)

        client.force_authenticate(user=None)
        for path in paths:
            with self.subTest(role="anonymous", path=path):
                self.assertEqual(client.get(path).status_code, 401)
