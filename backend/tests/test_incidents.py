from unittest.mock import patch

from api.models import User
from audit.models import AuditEntry
from audit.services import record
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from incidents.models import Incident
from rest_framework.test import APIClient


class IncidentModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guard = User.objects.create_user(
            email="incident-guard@test.cr", full_name="Guard", role=User.Role.GUARDA
        )

    def test_each_category_preserves_description_actor_and_automatic_time(self):
        before = timezone.now()
        for category in Incident.Category.values:
            with self.subTest(category=category):
                incident = Incident(
                    description="  Objeto encontrado junto a la entrada.  ",
                    category=category, user=self.guard,
                )
                incident.full_clean()
                incident.save()
                incident.refresh_from_db()
                self.assertEqual(incident.description, "Objeto encontrado junto a la entrada.")
                self.assertEqual((incident.category, incident.user_id), (category, self.guard.pk))
                self.assertLessEqual(before, incident.timestamp)
                self.assertLessEqual(incident.timestamp, timezone.now())
        self.assertEqual(Incident.objects.count(), 5)

    def test_description_minimum_counts_trimmed_characters(self):
        for description in ("", "123456789", " " * 10, " 123456789 ", "\t\n" * 10):
            with self.subTest(description=description):
                incident = Incident(description=description, category="otro", user=self.guard)
                with self.assertRaisesMessage(ValidationError, "10 caracteres"):
                    incident.full_clean()
        incident = Incident(description=" 1234567890 ", category="otro", user=self.guard)
        incident.full_clean()
        incident.save()
        self.assertEqual(incident.description, "1234567890")

    def test_database_rejects_invalid_description_category_and_missing_actor(self):
        valid = {"description": "1234567890", "category": "otro", "user": self.guard}
        for values in (
            {"description": ""}, {"description": "123456789"},
            {"description": " 123456789 "}, {"description": None},
            {"category": "invalid"}, {"category": ""}, {"category": None},
            {"user": None},
        ):
            with self.subTest(values=values):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Incident.objects.create(**{**valid, **values})
        self.assertFalse(Incident.objects.exists())

    def test_registering_account_cannot_be_deleted(self):
        incident = Incident.objects.create(
            description="1234567890", category="otro", user=self.guard,
        )
        self.assertTrue(self.guard.has_related_records())
        with self.assertRaises(ProtectedError):
            self.guard.delete()
        self.assertTrue(Incident.objects.filter(pk=incident.pk).exists())


class IncidentAPITests(TestCase):
    url = "/api/incidents/"

    @classmethod
    def setUpTestData(cls):
        cls.guard = User.objects.create_user(
            email="incident-guard@test.cr", full_name="Guard", role=User.Role.GUARDA
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.guard)
        self.payload = {
            "description": "Objeto encontrado junto a la entrada.",
            "category": "objeto_extraviado",
        }

    def test_each_category_is_saved_with_automatic_metadata_and_one_audit(self):
        before = timezone.now()
        for category in Incident.Category.values:
            with self.subTest(category=category):
                response = self.client.post(
                    self.url, {**self.payload, "category": category}, format="json",
                )
                self.assertEqual(response.status_code, 201, response.data)
                incident = Incident.objects.get(pk=response.data["id"])
                self.assertEqual(incident.description, self.payload["description"])
                self.assertEqual((incident.category, incident.user_id), (category, self.guard.pk))
                self.assertEqual(response.data["user"], self.guard.pk)
                self.assertIn("timestamp", response.data)
                self.assertLessEqual(before, incident.timestamp)
                self.assertLessEqual(incident.timestamp, timezone.now())
                audit = AuditEntry.objects.get(entity="incident", entity_id=str(incident.pk))
                self.assertEqual((audit.action_type, audit.user_id, audit.role), ("create", self.guard.pk, "guarda"))
                self.assertEqual(audit.changes["description"]["new"], incident.description)
                self.assertEqual(audit.changes["user"]["new"], self.guard.pk)
                self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual((Incident.objects.count(), AuditEntry.objects.count()), (5, 5))

    def test_description_validation_states_the_ten_character_minimum(self):
        payloads = [{"category": "otro"}]
        for description in (None, "", "123456789", " " * 10, " 123456789 ", "\t\n" * 10):
            payloads.append({**self.payload, "description": description})
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn("10 caracteres", str(response.data["description"]))
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(AuditEntry.objects.exists())
        response = self.client.post(
            self.url, {**self.payload, "description": " 1234567890 "}, format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Incident.objects.get().description, "1234567890")

    def test_invalid_categories_types_and_server_owned_or_extra_fields_are_rejected(self):
        invalid = [[], "text", {}, {"description": self.payload["description"]}]
        for category in ("unknown", "", None, [], {}, True):
            invalid.append({**self.payload, "category": category})
        for description in ([], {}, True):
            invalid.append({**self.payload, "description": description})
        for field in ("id", "user", "user_id", "timestamp", "status"):
            invalid.append({**self.payload, field: "forged"})
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(AuditEntry.objects.exists())

    def test_guard_and_admins_can_register_and_other_roles_are_denied(self):
        allowed = {User.Role.GUARDA, User.Role.ADMINISTRADOR_GENERAL, User.Role.ADMINISTRADOR_SISTEMA}
        for role in User.Role.values:
            with self.subTest(role=role):
                account = User.objects.create_user(
                    email=f"{role}@test.cr", full_name=role, role=role,
                )
                self.client.force_authenticate(account)
                response = self.client.post(self.url, self.payload, format="json")
                self.assertEqual(response.status_code, 201 if role in allowed else 403, response.data)
                if role in allowed:
                    incident = Incident.objects.get(pk=response.data["id"])
                    audit = AuditEntry.objects.get(entity="incident", entity_id=str(incident.pk))
                    self.assertEqual(incident.user_id, account.pk)
                    self.assertEqual((audit.user_id, audit.role), (account.pk, role))
        self.assertEqual(Incident.objects.count(), 3)
        self.assertEqual(AuditEntry.objects.filter(entity="incident").count(), 3)
        self.assertEqual(AuditEntry.objects.filter(entity="access").count(), 2)

    def test_anonymous_and_inactive_accounts_cannot_register(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 401)
        for role in (User.Role.GUARDA, User.Role.ADMINISTRADOR_GENERAL, User.Role.ADMINISTRADOR_SISTEMA):
            with self.subTest(role=role):
                account = User.objects.create_user(
                    email=f"inactive-{role}@test.cr", full_name=role, role=role, is_active=False,
                )
                self.client.force_authenticate(account)
                self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 403)
        self.assertFalse(Incident.objects.exists())

    def test_failure_rolls_back_incident_and_audit_and_allows_retry(self):
        def fail_after_audit(**kwargs):
            record(**kwargs)
            raise RuntimeError("private failure details")

        for target, failure in (
            ("incidents.models.Incident.save", IntegrityError("private DB details")),
            ("audit.services.record", fail_after_audit),
        ):
            with self.subTest(target=target):
                with patch(target, side_effect=failure):
                    with self.assertLogs("incidents.views", level="ERROR"):
                        response = self.client.post(self.url, self.payload, format="json")
                self.assertEqual(response.status_code, 503, response.data)
                self.assertEqual(response.data["code"], "incident_save_failed")
                self.assertIn("Inténtelo de nuevo", response.data["detail"])
                self.assertNotIn("private", str(response.data))
                self.assertFalse(Incident.objects.exists())
                self.assertFalse(AuditEntry.objects.exists())
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 201)
        self.assertEqual((Incident.objects.count(), AuditEntry.objects.count()), (1, 1))

    def test_saved_incident_cannot_be_read_edited_or_deleted_through_registration(self):
        response = self.client.post(self.url, self.payload, format="json")
        incident = Incident.objects.get(pk=response.data["id"])
        timestamp = incident.timestamp
        for method in ("get", "put", "patch", "delete"):
            for url, expected in ((self.url, 405), (f"{self.url}{incident.pk}/", 404)):
                with self.subTest(method=method, url=url):
                    response = getattr(self.client, method)(url, {"description": "Changed description"}, format="json")
                    self.assertEqual(response.status_code, expected)
        incident.refresh_from_db()
        self.assertEqual(incident.description, self.payload["description"])
        self.assertEqual((incident.timestamp, incident.user_id), (timestamp, self.guard.pk))
        self.assertEqual((Incident.objects.count(), AuditEntry.objects.count()), (1, 1))

    def test_real_session_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.guard)
        self.assertEqual(client.post(self.url, self.payload, format="json").status_code, 403)
        self.assertFalse(Incident.objects.exists())
        csrf = client.get("/api/auth/csrf/").data["csrfToken"]
        response = client.post(self.url, self.payload, format="json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 201, response.data)
