from copy import deepcopy
from unittest.mock import patch

from api.models import User
from audit.models import AuditEntry
from django.test import TestCase
from rest_framework.test import APIClient
from system_configuration.defaults import DEFAULTS
from system_configuration.models import Parameter


class ConfigurationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            email="admin@test.cr", full_name="Admin", role="administrador_sistema"
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_defaults_and_change_visible_on_next_public_load(self):
        self.assertEqual(self.client.get("/api/public/configuration/").data, DEFAULTS)
        hours = deepcopy(DEFAULTS["opening_hours"])
        hours["2"]["opens"] = "08:00"
        values = {
            "museum_name": "SIAM",
            "opening_hours": hours,
            "default_language": "en",
        }
        response = self.client.patch("/api/configuration/", values, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(AuditEntry.objects.count(), 3)
        self.client.force_authenticate(user=None)
        public = self.client.get("/api/public/configuration/")
        self.assertEqual(public.data["opening_hours"]["2"]["opens"], "08:00")
        self.assertEqual(public.data["museum_name"], "SIAM")
        self.assertEqual(public.data["default_language"], "en")
        self.assertIn("no-cache", public["Cache-Control"])

    def test_all_defaults_restore_and_noop_has_no_change_entry(self):
        values = {
            "museum_name": "New",
            "address": "New address",
            "location": "New location",
            "default_language": "en",
            "opening_hours": {
                str(d): {"opens": None, "closes": None} for d in range(7)
            },
        }
        self.assertEqual(
            self.client.patch("/api/configuration/", values, format="json").status_code,
            200,
        )
        for key in DEFAULTS:
            response = self.client.post(
                f"/api/configuration/{key}/reset/", {}, format="json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data[key], DEFAULTS[key])
            entry = AuditEntry.objects.first()
            self.assertEqual(entry.entity_id, key)
            self.assertEqual(
                entry.changes[key], {"old": values[key], "new": DEFAULTS[key]}
            )
            self.assertEqual(entry.user_id, self.admin.pk)
        self.assertEqual(AuditEntry.objects.count(), 10)
        self.client.patch("/api/configuration/", DEFAULTS, format="json")
        self.assertEqual(AuditEntry.objects.count(), 10)
        self.assertEqual(
            self.client.post("/api/configuration/unknown/reset/").status_code, 404
        )

    def test_field_validation_and_no_partial_saves(self):
        for value in ("09:00", "08:00", "25:00", "abc"):
            hours = deepcopy(DEFAULTS["opening_hours"])
            hours["2"] = {"opens": "09:00", "closes": value}
            response = self.client.patch(
                "/api/configuration/",
                {"museum_name": "Do not save", "opening_hours": hours},
                format="json",
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("closes", str(response.data["opening_hours"]))
        for data in (
            {"default_language": "fr"},
            {"museum_name": " "},
            {"address": ""},
            {"opening_hours": {}},
            {"unknown": "value"},
        ):
            self.assertEqual(
                self.client.patch(
                    "/api/configuration/", data, format="json"
                ).status_code,
                400,
            )
        self.assertFalse(Parameter.objects.exists())
        self.assertFalse(AuditEntry.objects.exists())

    def test_audit_failure_rolls_back_all_parameters(self):
        with patch(
            "system_configuration.services.record",
            side_effect=RuntimeError("audit failed"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.patch(
                    "/api/configuration/",
                    {"museum_name": "New", "address": "New address"},
                    format="json",
                )
        self.assertFalse(Parameter.objects.exists())

    def test_only_system_admin_can_manage(self):
        for role in User.Role.values + [None]:
            if role == "administrador_sistema":
                continue
            self.admin.role = role or "guarda"
            self.client.force_authenticate(self.admin if role else None)
            expected = 403 if role else 401
            self.assertEqual(self.client.get("/api/configuration/").status_code, expected)
            self.assertEqual(
                self.client.patch(
                    "/api/configuration/", {"museum_name": "Forbidden"}, format="json"
                ).status_code,
                expected,
            )
            self.assertEqual(
                self.client.post("/api/configuration/museum_name/reset/").status_code,
                expected,
            )

    def test_patch_rejects_incomplete_or_unknown_day_fields(self):
        for invalid in (
            {"opens": "09:00"},
            {"closes": "17:00"},
            {},
            {"opens": "09:00", "closes": "17:00", "extra": 1},
        ):
            with self.subTest(day=invalid):
                hours = deepcopy(DEFAULTS["opening_hours"])
                hours["2"] = invalid
                response = self.client.patch(
                    "/api/configuration/", {"opening_hours": hours}, format="json"
                )
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn("2", response.data["opening_hours"])
        self.assertFalse(Parameter.objects.exists())
        self.assertFalse(AuditEntry.objects.exists())
