from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from audit.models import AuditEntry
from .models import Photo, Piece


class PhotoDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="curator@example.com", full_name="Curator", role=User.Role.MUSEOLOGO,
        )
        self.piece = Piece.objects.create(title="Test piece")
        self.photo = Photo.objects.create(piece=self.piece, name="Photo", content=b"image")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f"/api/pieces/{self.piece.pk}/photos/{self.photo.pk}/"

    def test_deletes_only_selected_photo_and_records_history(self):
        other = Photo.objects.create(piece=self.piece, name="Keep", content=b"keep")
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"deleted": self.photo.pk})
        self.assertFalse(Photo.objects.filter(pk=self.photo.pk).exists())
        self.assertTrue(Photo.objects.filter(pk=other.pk).exists())
        entry = AuditEntry.objects.get(entity="piece", entity_id=str(self.piece.pk))
        self.assertEqual(entry.user_id, self.user.pk)
        self.assertEqual(entry.action_type, AuditEntry.Action.MODIFY)
        self.assertEqual(entry.changes["photos"]["old"], [self.photo.pk, other.pk])
        self.assertEqual(entry.changes["photos"]["new"], [other.pk])
        self.assertNotIn("content", entry.changes.get("photo", {}).get("old", {}))

    def test_rejects_anonymous_and_unauthorized_users(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        for role in [User.Role.GUARDA, User.Role.COORDINADOR]:
            self.user.role = role
            self.client.force_authenticate(self.user)
            self.assertEqual(self.client.delete(self.url).status_code, 403)
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_photo_must_belong_to_requested_piece(self):
        other_piece = Piece.objects.create(title="Other piece")
        response = self.client.delete(f"/api/pieces/{other_piece.pk}/photos/{self.photo.pk}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_audit_failure_rolls_back_deletion(self):
        with patch("collection.views.record", side_effect=RuntimeError("Audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.delete(self.url)
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())

    def test_session_authenticated_deletion_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.delete(self.url).status_code, 403)
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())
