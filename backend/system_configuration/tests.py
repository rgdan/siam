from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from audit.models import AuditEntry
from .defaults import DEFAULTS
from .models import Parameter


class ConfigurationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            email="settings@example.com", full_name="Settings admin",
            role=User.Role.ADMINISTRADOR_SISTEMA,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_public_defaults_do_not_require_a_session(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/public/configuration/").json(), DEFAULTS)
        self.assertEqual(self.client.get("/api/configuration/").status_code, 401)
        self.assertEqual(self.client.patch("/api/configuration/", {}, format="json").status_code, 401)

    def test_only_system_administrator_can_read_update_or_reset(self):
        for role in User.Role:
            user = User.objects.create_user(email=f"{role}@example.com", full_name=role, role=role)
            self.client.force_authenticate(user)
            expected = 200 if role == User.Role.ADMINISTRADOR_SISTEMA else 403
            with self.subTest(role=role):
                self.assertEqual(self.client.get("/api/configuration/").status_code, expected)
                self.assertEqual(self.client.patch("/api/configuration/", {"location": "Alajuela"}, format="json").status_code, expected)
                self.assertEqual(self.client.post("/api/configuration/location/reset/").status_code, expected)

    def test_save_persists_all_settings_and_records_each_change(self):
        values = deepcopy(DEFAULTS)
        values.update(museum_name="Museum", address="Central street", location="Heredia", default_language="en")
        values["opening_hours"]["1"] = {"opens": "10:00", "closes": "16:00"}
        values["opening_hours"]["0"] = {"opens": None, "closes": None}
        response = self.client.patch("/api/configuration/", values, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"values": values, "defaults": DEFAULTS})
        self.assertEqual(self.client.get("/api/public/configuration/").json(), values)
        changes = AuditEntry.objects.filter(entity="system_parameter")
        self.assertEqual(changes.count(), 5)
        self.assertTrue(all(entry.user_id == self.admin.pk for entry in changes))
        self.client.patch("/api/configuration/", values, format="json")
        self.assertEqual(changes.count(), 5)

    def test_invalid_settings_do_not_change_saved_values(self):
        for values in [
            {"museum_name": ""}, {"default_language": "fr"}, {"unknown": "value"},
            {"opening_hours": {"0": {"opens": "09:00", "closes": "17:00"}}},
            *({"opening_hours": {**deepcopy(DEFAULTS["opening_hours"]), "0": hours}} for hours in [
                {"opens": "17:00", "closes": "09:00"},
                {"opens": "09:00", "closes": None},
                {"opens": "25:00", "closes": "26:00"},
            ]),
        ]:
            with self.subTest(values=values):
                self.assertEqual(self.client.patch("/api/configuration/", values, format="json").status_code, 400)
                self.assertEqual(self.client.get("/api/public/configuration/").json(), DEFAULTS)
        self.assertEqual(Parameter.objects.count(), 0)

    def test_reset_changes_only_requested_setting(self):
        self.client.patch("/api/configuration/", {"museum_name": "Custom", "location": "Heredia"}, format="json")
        response = self.client.post("/api/configuration/museum_name/reset/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["museum_name"], DEFAULTS["museum_name"])
        self.assertEqual(response.json()["location"], "Heredia")
        self.assertEqual(self.client.post("/api/configuration/unknown/reset/").status_code, 404)

    def test_audit_failure_rolls_back_settings(self):
        with patch("system_configuration.services.record", side_effect=RuntimeError("Audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.patch("/api/configuration/", {"location": "Heredia"}, format="json")
        self.assertEqual(Parameter.objects.count(), 0)

    def test_authenticated_updates_require_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.patch("/api/configuration/", {"location": "Heredia"}, format="json").status_code, 403)
