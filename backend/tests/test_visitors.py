from itertools import product
from unittest.mock import patch

from api.models import User
from audit.models import AuditEntry
from audit.services import record
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from visitors.models import VisitorEntry


class VisitorEntryModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guard = User.objects.create_user(
            email="guard@test.cr", full_name="Guard", role=User.Role.GUARDA
        )

    def test_each_combination_preserves_categories_time_and_guard(self):
        before = timezone.now()
        for age_group, nationality, sex in product(
            VisitorEntry.AgeGroup.values,
            VisitorEntry.Nationality.values,
            VisitorEntry.Sex.values,
        ):
            with self.subTest(age_group=age_group, nationality=nationality, sex=sex):
                entry = VisitorEntry.objects.create(
                    age_group=age_group,
                    nationality=nationality,
                    sex=sex,
                    user=self.guard,
                )
                entry.refresh_from_db()
                self.assertEqual(
                    (entry.age_group, entry.nationality, entry.sex, entry.user_id),
                    (age_group, nationality, sex, self.guard.pk),
                )
                self.assertLessEqual(before, entry.timestamp)
                self.assertLessEqual(entry.timestamp, timezone.now())
        self.assertEqual(VisitorEntry.objects.count(), 8)

    def test_database_rejects_invalid_or_missing_categories_and_guard(self):
        valid = {
            "age_group": "mayor",
            "nationality": "nacional",
            "sex": "femenino",
            "user": self.guard,
        }
        for field in ("age_group", "nationality", "sex", "user"):
            invalid_values = (None,) if field == "user" else ("invalid", "", None)
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        VisitorEntry.objects.create(**{**valid, field: value})
        self.assertEqual(VisitorEntry.objects.count(), 0)

    def test_entry_prevents_deleting_registering_guard(self):
        entry = VisitorEntry.objects.create(
            age_group="menor", nationality="extranjero", sex="masculino",
            user=self.guard,
        )
        self.assertTrue(self.guard.has_related_records())
        with self.assertRaises(ProtectedError):
            self.guard.delete()
        self.assertTrue(VisitorEntry.objects.filter(pk=entry.pk).exists())


class VisitorEntryAPITests(TestCase):
    url = "/api/visitor-entries/"

    @classmethod
    def setUpTestData(cls):
        cls.guard = User.objects.create_user(
            email="guard@test.cr", full_name="Guard", role=User.Role.GUARDA
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.guard)
        self.payload = {
            "age_group": "mayor", "nationality": "extranjero", "sex": "femenino",
        }

    def test_registration_returns_created_entry_and_exactly_one_audit(self):
        before = timezone.now()
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        entry = VisitorEntry.objects.get()
        self.assertEqual(response.data["id"], entry.pk)
        self.assertEqual(response.data["user"], self.guard.pk)
        self.assertIn("timestamp", response.data)
        self.assertLessEqual(before, entry.timestamp)
        self.assertLessEqual(entry.timestamp, timezone.now())
        for field, value in self.payload.items():
            self.assertEqual(getattr(entry, field), value)
            self.assertEqual(response.data[field], value)
        audit = AuditEntry.objects.get()
        self.assertEqual(
            (audit.entity, audit.entity_id, audit.action_type, audit.user_id, audit.role),
            ("visitor_entry", str(entry.pk), "create", self.guard.pk, "guarda"),
        )
        self.assertEqual(audit.changes["sex"]["new"], "femenino")
        self.assertEqual(audit.changes["user"]["new"], self.guard.pk)
        self.assertIn("no-store", response["Cache-Control"])

    def test_invalid_missing_or_extra_fields_create_no_entry_or_audit(self):
        invalid = [None, [], "text", {}]
        for field in self.payload:
            for value in ("invalid", "", None, [], {}, True, 1):
                invalid.append({**self.payload, field: value})
            invalid.append({k: v for k, v in self.payload.items() if k != field})
        for field in ("id", "user", "user_id", "timestamp", "name", "id_number"):
            invalid.append({**self.payload, field: "forged"})
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(VisitorEntry.objects.exists())
        self.assertFalse(AuditEntry.objects.exists())

    def test_other_roles_are_denied_even_administrators(self):
        for role in User.Role.values:
            if role == User.Role.GUARDA:
                continue
            with self.subTest(role=role):
                account = User.objects.create_user(
                    email=f"{role}@test.cr", full_name=role, role=role,
                )
                self.client.force_authenticate(account)
                response = self.client.post(self.url, self.payload, format="json")
                self.assertEqual(response.status_code, 403, response.data)
        self.assertFalse(VisitorEntry.objects.exists())
        self.assertEqual(AuditEntry.objects.filter(entity="access").count(), 4)
        self.assertFalse(AuditEntry.objects.filter(entity="visitor_entry").exists())

    def test_missing_session_and_inactive_guard_are_denied(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.post(self.url, self.payload, format="json").status_code, 401,
        )
        self.guard.is_active = False
        self.client.force_authenticate(self.guard)
        self.assertEqual(
            self.client.post(self.url, self.payload, format="json").status_code, 403,
        )
        self.assertFalse(VisitorEntry.objects.exists())

    def test_save_failure_rolls_back_and_allows_retry(self):
        def fail_after_audit(**kwargs):
            record(**kwargs)
            raise RuntimeError("private failure details")

        for target, failure in (
            ("visitors.models.VisitorEntry.save", IntegrityError("private DB details")),
            ("audit.services.record", fail_after_audit),
        ):
            with self.subTest(target=target):
                with patch(target, side_effect=failure):
                    with self.assertLogs("visitors.views", level="ERROR"):
                        response = self.client.post(self.url, self.payload, format="json")
                self.assertEqual(response.status_code, 503, response.data)
                self.assertEqual(response.data["code"], "visitor_entry_save_failed")
                self.assertIn("Inténtelo de nuevo", response.data["detail"])
                self.assertNotIn("private", str(response.data))
                self.assertFalse(VisitorEntry.objects.exists())
                self.assertFalse(AuditEntry.objects.exists())
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(VisitorEntry.objects.count(), 1)
        self.assertEqual(AuditEntry.objects.count(), 1)

    def test_only_post_is_available(self):
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
        self.assertFalse(VisitorEntry.objects.exists())

    def test_session_authentication_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.guard)
        response = client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(VisitorEntry.objects.exists())
        token = client.get("/api/auth/csrf/").data["csrfToken"]
        response = client.post(
            self.url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201, response.data)
