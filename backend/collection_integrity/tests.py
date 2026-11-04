from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from api.models import User
from audit.models import AuditEntry
from .models import Piece, Photo
from .services import decommission_piece


class DecommissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="museum@example.com", full_name="Museum", role="museologo")
        self.piece = Piece.objects.create(title="Test", state="displayed", location="Room 1")
        self.photo = Photo.objects.create(piece=self.piece, name="original", content=b"original")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f"/api/pieces/{self.piece.pk}/decommission/"

    def test_preserves_piece_photos_and_history(self):
        response = self.client.post(self.url, {"reason": "Damage", "confirmed": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "decommissioned")
        self.assertEqual(self.piece.location, "")
        self.assertEqual(self.piece.decommissioned_by, self.user)
        self.assertIsNotNone(self.piece.decommissioned_at)
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())
        detail = self.client.get(f"/api/pieces/{self.piece.pk}/").json()
        self.assertEqual(detail["decommission_reason"], "Damage")
        self.assertEqual(len(detail["history"]), 1)
        self.assertEqual(detail["history"][0]["changes"]["state"], {"old": "displayed", "new": "decommissioned"})
        self.assertEqual(self.client.patch(f"/api/pieces/{self.piece.pk}/", {"state": "stored"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(self.url, {"reason": "Again", "confirmed": True}, format="json").status_code, 400)

    def test_confirmation_and_reason_required(self):
        for payload in ({"reason": "x"}, {"reason": "x", "confirmed": False}, {"reason": " ", "confirmed": True}):
            self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 400)
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "displayed")

    def test_other_roles_denied(self):
        for role in User.Role.values:
            if role == "museologo":
                continue
            self.user.role = role
            self.user.save()
            self.assertEqual(self.client.post(self.url, {"reason": "x", "confirmed": True}, format="json").status_code, 403)

    def test_audit_failure_rolls_back(self):
        with patch("collection_integrity.services.record", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                decommission_piece(user=self.user, piece_id=self.piece.pk, reason="Damage", confirmed=True)
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "displayed")
        self.assertFalse(self.piece.decommissioned)
        self.assertEqual(self.piece.location, "Room 1")
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())


    def test_reactivation_restores_storage_and_preserves_history_and_photos(self):
        self.client.post(self.url, {"reason": "Damage", "confirmed": True}, format="json")
        response = self.client.post(f"/api/pieces/{self.piece.pk}/reactivate/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.location, self.piece.decommissioned), ("stored", "", False))
        self.assertEqual(self.piece.title, "Test")
        self.assertEqual(self.piece.photos.get().content, b"original")
        self.assertIsNone(self.piece.decommissioned_at)
        self.assertIsNone(self.piece.decommissioned_by)
        self.assertEqual(self.piece.decommission_reason, "")
        entries = AuditEntry.objects.filter(entity="piece", entity_id=str(self.piece.pk))
        self.assertEqual(entries.count(), 2)
        latest = entries.latest("timestamp")
        self.assertEqual(latest.changes["state"], {"old": "decommissioned", "new": "stored"})
        self.assertEqual(latest.changes["decommissioned"], {"old": True, "new": False})
        self.assertTrue(entries.filter(action_type="decommission", changes__decommission_reason__new="Damage").exists())
        self.assertEqual(self.client.patch(f"/api/pieces/{self.piece.pk}/", {"title": "Editable again"}, format="json").status_code, 200)
        self.assertEqual(self.client.post(f"/api/pieces/{self.piece.pk}/reactivate/", {}, format="json").status_code, 400)

    def test_reactivation_rejects_active_pieces(self):
        response = self.client.post(f"/api/pieces/{self.piece.pk}/reactivate/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "displayed")
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_reactivation_denies_other_roles_and_unknown_piece(self):
        decommission_piece(user=self.user, piece_id=self.piece.pk, reason="Damage", confirmed=True)
        for role in User.Role.values:
            if role == "museologo":
                continue
            self.user.role = role
            self.user.save()
            self.assertEqual(self.client.post(f"/api/pieces/{self.piece.pk}/reactivate/", {}, format="json").status_code, 403)
        self.piece.refresh_from_db()
        self.assertTrue(self.piece.decommissioned)
        self.user.role = "museologo"
        self.user.save()
        self.assertEqual(self.client.post("/api/pieces/999999/reactivate/", {}, format="json").status_code, 404)

    def test_reactivation_audit_failure_rolls_back(self):
        decommission_piece(user=self.user, piece_id=self.piece.pk, reason="Damage", confirmed=True)
        with patch("collection_integrity.services.record", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(f"/api/pieces/{self.piece.pk}/reactivate/", {}, format="json")
        self.piece.refresh_from_db()
        self.assertTrue(self.piece.decommissioned)
        self.assertEqual(self.piece.state, "decommissioned")
        self.assertEqual(self.piece.decommission_reason, "Damage")

    def test_reactivation_service_enforces_role(self):
        from rest_framework.exceptions import PermissionDenied
        from .services import reactivate_piece
        self.user.role = "administrador_general"
        with self.assertRaises(PermissionDenied):
            reactivate_piece(user=self.user, piece_id=self.piece.pk)
