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
