from datetime import timedelta
from unittest.mock import patch

from api.models import User
from audit.models import AuditEntry
from audit.services import audited_create, record
from collection_integrity.models import Piece
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient


class AuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            email="admin@test.cr",
            password="Example123",
            full_name="Admin",
            role=User.Role.ADMINISTRADOR_SISTEMA,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_account_creation_logs_exactly_once_without_password(self):
        result = self.client.post(
            "/api/users/",
            {
                "email": "new@test.cr",
                "password": "Private123",
                "full_name": "New",
                "role": "guarda",
            },
            format="json",
        )
        self.assertEqual(result.status_code, 201, result.data)
        entry = AuditEntry.objects.get()
        self.assertEqual(
            (entry.entity, entry.entity_id, entry.user_id),
            ("user", str(result.data["id"]), self.admin.pk),
        )
        self.assertNotIn("password", str(entry.changes))
        self.assertNotIn("Private123", str(entry.changes))

    def test_visitor_and_event_callback_contract_one_entry_each(self):

        for entity in ("visitor_entry", "event"):
            with self.subTest(entity=entity):
                before = AuditEntry.objects.count()
                obj = audited_create(
                    user=self.admin,
                    entity=entity,
                    create=lambda entity=entity: Piece.objects.create(title=entity),
                )
                self.assertEqual(AuditEntry.objects.count(), before + 1)
                self.assertEqual(AuditEntry.objects.first().entity_id, str(obj.pk))

    def test_callback_rolls_back_if_audit_fails(self):
        with patch(
            "audit.services.record", side_effect=RuntimeError("audit unavailable")
        ):
            with self.assertRaises(RuntimeError):
                audited_create(
                    user=self.admin,
                    entity="event",
                    create=lambda: Piece.objects.create(title="event"),
                )
        self.assertFalse(Piece.objects.exists())

    def test_recursive_redaction_and_changed_fields(self):
        entry = record(
            user=self.admin,
            action_type="modify",
            entity="user",
            entity_id=1,
            old={
                "name": "Old",
                "same": 1,
                "password": "hash1",
                "nested": {"reset_token": "abc", "x": 1},
            },
            new={
                "name": "New",
                "same": 1,
                "password": "hash2",
                "nested": {"newPassword": "xyz", "x": 2},
            },
        )
        self.assertEqual(
            entry.changes,
            {
                "name": {"old": "Old", "new": "New"},
                "nested": {"old": {"x": 1}, "new": {"x": 2}},
            },
        )
        self.assertEqual(entry.role, "administrador_sistema")
        self.admin.role = "guarda"
        self.admin.save()
        entry.refresh_from_db()
        self.assertEqual(entry.role, "administrador_sistema")

    def test_login_and_failed_login(self):
        self.client.force_authenticate(user=None)
        good = self.client.post(
            "/api/auth/login/",
            {"email": self.admin.email, "password": "Example123"},
            format="json",
        )
        self.assertEqual(good.status_code, 200, good.data)
        self.client.logout()
        bad = self.client.post(
            "/api/auth/login/",
            {"email": "unknown@test.cr", "password": "Private123"},
            format="json",
        )
        self.assertEqual(bad.status_code, 401)
        self.assertEqual(
            list(AuditEntry.objects.values_list("action_type", flat=True)),
            ["failed_login", "login"],
        )
        self.assertIsNone(AuditEntry.objects.first().user_id)
        malformed = self.client.post("/api/auth/login/", {}, format="json")
        self.assertEqual(malformed.status_code, 401)
        self.assertEqual(
            AuditEntry.objects.filter(action_type="failed_login").count(), 2
        )

    def test_filter_pagination_and_order(self):
        for i in range(55):
            record(user=self.admin, action_type="create", entity="piece", entity_id=i)
        record(user=None, action_type="failed_login", entity="user")
        today = timezone.localdate().isoformat()
        query = f"/api/audit/?user={self.admin.pk}&action_type=create&entity=piece&date_from={today}&date_to={today}"
        response = self.client.get(query)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 55)
        self.assertEqual(len(response.data["results"]), 50)
        self.assertEqual(response.data["results"][0]["entity_id"], "54")
        second = self.client.get(query + "&page=2")
        self.assertEqual(len(second.data["results"]), 5)
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        self.assertEqual(
            self.client.get("/api/audit/?date_from=" + tomorrow).data["count"], 0
        )
        for query in (
            "user=no",
            "action_type=no",
            "date_from=no",
            f"date_from={tomorrow}&date_to={today}",
        ):
            self.assertEqual(self.client.get("/api/audit/?" + query).status_code, 400)

    def test_read_only_model_and_endpoint(self):
        entry = record(user=self.admin, action_type="create", entity="piece")
        for method in ("post", "patch", "put", "delete"):
            self.assertEqual(
                getattr(self.client, method)(
                    "/api/audit/", {}, format="json"
                ).status_code,
                405,
            )
        for operation in (
            entry.save,
            entry.delete,
            lambda: AuditEntry.objects.all().delete(),
            lambda: AuditEntry.objects.all().update(entity="tamper"),
        ):
            with self.assertRaises(ValidationError):
                operation()

    def test_other_roles_get_403_and_public_gets_401(self):
        for role in User.Role.values:
            if role == "administrador_sistema":
                continue
            self.admin.role = role
            self.client.force_authenticate(self.admin)
            self.assertEqual(self.client.get("/api/audit/").status_code, 403)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/audit/").status_code, 401)

    def test_denied_access_records_function_actor_and_time(self):
        self.admin.role = "guarda"
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(set(response.data), {"detail"})
        entry = AuditEntry.objects.get()
        self.assertEqual((entry.user_id, entry.role), (self.admin.pk, "guarda"))
        self.assertEqual(entry.changes["function"]["new"], "usuarios.consultar")
        self.assertEqual(entry.changes["outcome"]["new"], "denied")
        self.assertIsNotNone(entry.timestamp)

    def test_delete_audits_and_preserves_piece_and_audit_history(self):
        from collection_integrity.services import register_piece

        unused = User.objects.create_user(email="unused@test.cr", full_name="Unused", role="guarda")
        target = User.objects.create_user(email="museum@test.cr", full_name="Museum", role="museologo")
        piece = register_piece(user=target, title="Conservar")
        for account, action in ((unused, "deleted"), (target, "deactivated")):
            account_id = account.pk
            response = self.client.delete(f"/api/users/{account_id}/", {"confirm": True}, format="json")
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["action"], action)
            entry = AuditEntry.objects.first()
            self.assertEqual((entry.action_type, entry.entity_id, entry.user_id), ("decommission", str(account_id), self.admin.pk))
        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertEqual(piece.history.get().user_id, target.pk)
        self.assertTrue(AuditEntry.objects.filter(user=target).exists())

    def test_delete_rolls_back_if_audit_fails(self):
        target = User.objects.create_user(email="keep@test.cr", full_name="Keep", role="guarda")
        with patch("api.views.record", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                self.client.delete(f"/api/users/{target.pk}/", {"confirm": True}, format="json")
        self.assertTrue(User.objects.filter(pk=target.pk, is_active=True).exists())

    def test_denial_after_transaction_recheck_keeps_audit(self):
        with patch("api.views.permisos_para", return_value=frozenset()):
            response = self.client.patch(f"/api/users/{self.admin.pk}/", {"full_name": "Not saved"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AuditEntry.objects.get().changes["function"]["new"], "usuarios.actualizar")
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.full_name, "Admin")

    def test_role_change_and_reset_have_safe_audit_details(self):
        target = User.objects.create_user(email="role@test.cr", full_name="Role", role="guarda")
        session = APIClient()
        session.force_login(target)
        role_change = self.client.patch(f"/api/users/{target.pk}/", {"role": "coordinador"}, format="json")
        self.assertEqual(role_change.status_code, 200, role_change.data)
        self.assertEqual(session.get("/api/auth/me/").data["role"], "coordinador")
        self.assertEqual(AuditEntry.objects.first().changes["role"], {"old": "guarda", "new": "coordinador"})
        response = self.client.patch(f"/api/users/{target.pk}/", {"role": "coordinador", "password": "Private456"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        entry = AuditEntry.objects.first()
        self.assertEqual(session.get("/api/auth/me/").status_code, 401)
        self.assertEqual(entry.changes["credential_reset"]["new"], True)
        self.assertNotIn("Private456", str(entry.changes))
        self.assertNotIn("password", str(entry.changes))

    def test_password_update_and_known_failed_actor(self):
        account = User.objects.create_user(
            email="guard@test.cr",
            password="Example123",
            full_name="Guard",
            role="guarda",
        )
        result = self.client.patch(
            f"/api/users/{account.pk}/",
            {"full_name": "Updated", "password": "NewPrivate456"},
            format="json",
        )
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(
            AuditEntry.objects.get().changes["full_name"],
            {"old": "Guard", "new": "Updated"},
        )
        self.assertNotIn("password", str(AuditEntry.objects.get().changes))
        self.client.force_authenticate(user=None)
        result = self.client.post(
            "/api/auth/login/",
            {"email": account.email, "password": "wrong"},
            format="json",
        )
        self.assertEqual(result.status_code, 401)
        entry = AuditEntry.objects.first()
        self.assertEqual(
            (entry.user_id, entry.role, entry.entity_id),
            (account.pk, "guarda", str(account.pk)),
        )

    def test_spanish_password_keys_are_removed(self):
        entry = record(
            user=self.admin,
            action_type="modify",
            entity="user",
            new={"contraseña": "Private123", "contraseña_nueva": "Secret456"},
        )
        self.assertEqual(entry.changes, {})
