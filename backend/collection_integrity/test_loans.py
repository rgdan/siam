from datetime import date
from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from api.models import User
from audit.models import AuditEntry
from .models import Photo, Piece
from .services import loan_piece, return_piece


class LoanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="museum@example.com", full_name="Museum", role=User.Role.MUSEOLOGO,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.piece = Piece.objects.create(title="Original", state="displayed", location="Room 1")
        self.photo = Photo.objects.create(piece=self.piece, name="Original", content=b"original")
        self.loan_url = f"/api/pieces/{self.piece.pk}/loan/"
        self.return_url = f"/api/pieces/{self.piece.pk}/return/"
        self.detail_url = f"/api/pieces/{self.piece.pk}/"
        self.payload = {"recipient": "Museum B", "start_date": "2026-01-01", "end_date": "2026-01-02"}

    def test_loan_from_storage_or_display_preserves_data(self):
        for state in ["stored", "displayed"]:
            with self.subTest(state=state):
                piece = Piece.objects.create(title="Original", state=state, location="Room 1" if state == "displayed" else "")
                photo = Photo.objects.create(piece=piece, name="Original", content=b"original")
                response = self.client.post(f"/api/pieces/{piece.pk}/loan/", self.payload, format="json")
                self.assertEqual(response.status_code, 200)
                piece.refresh_from_db()
                self.assertEqual((piece.state, piece.location, piece.title), ("loaned", "", "Original"))
                self.assertEqual((piece.loan_to, piece.loan_start, piece.loan_end), ("Museum B", date(2026, 1, 1), date(2026, 1, 2)))
                self.assertTrue(Photo.objects.filter(pk=photo.pk).exists())
                entry = AuditEntry.objects.get(entity="piece", entity_id=str(piece.pk))
                self.assertEqual(entry.user, self.user)
                self.assertIsNotNone(entry.timestamp)
                self.assertEqual(entry.changes["state"], {"old": state, "new": "loaned"})

    def test_return_preserves_loan_in_history(self):
        self.assertEqual(self.client.post(self.loan_url, self.payload, format="json").status_code, 200)
        self.assertEqual(self.client.get(self.detail_url).json()["loan_to"], "Museum B")
        self.assertEqual(self.client.post(self.return_url, {}, format="json").status_code, 200)
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.location, self.piece.loan_to), ("stored", "", ""))
        self.assertIsNone(self.piece.loan_start)
        self.assertIsNone(self.piece.loan_end)
        history = self.client.get(self.detail_url).json()["history"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["user"], self.user.full_name)
        self.assertEqual(history[0]["changes"]["state"], {"old": "loaned", "new": "stored"})
        self.assertEqual(history[0]["changes"]["loan_to"]["old"], "Museum B")
        self.assertEqual(history[0]["changes"]["loan_start"]["old"], "2026-01-01")
        self.assertEqual(history[0]["changes"]["loan_end"]["old"], "2026-01-02")
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())

    def test_equal_start_and_end_dates_are_valid(self):
        response = self.client.post(self.loan_url, self.payload | {"end_date": "2026-01-01"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_missing_fields_invalid_dates_and_reversed_period_are_rejected(self):
        cases = [self.payload | {"recipient": value} for value in ["", " ", "x" * 201]]
        cases += [self.payload | {key: value} for key in ["start_date", "end_date"] for value in ["", None, "invalid", "2026-02-30"]]
        cases += [{key: value for key, value in self.payload.items() if key != field} for field in self.payload]
        cases += [self.payload | {"end_date": "2025-12-31"}]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post(self.loan_url, payload, format="json")
                self.assertEqual(response.status_code, 400)
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.location), ("displayed", "Room 1"))
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_decommissioned_piece_is_rejected_with_reason(self):
        self.piece.decommissioned = True
        self.piece.save()
        response = self.client.post(self.loan_url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "cannot_loan_decommissioned")

    def test_stolen_and_lost_states_are_rejected_before_mutation(self):
        # These states are introduced by the separate SIAM-26 PR. Simulate the locked
        # record without requiring that PR's schema to verify the transition rule.
        for state in ["stolen", "lost"]:
            with self.subTest(state=state):
                with patch("collection_integrity.services.Piece.objects.select_for_update") as locked:
                    locked.return_value.get.return_value = Piece(pk=self.piece.pk, title="Original", state=state)
                    response = self.client.post(self.loan_url, self.payload, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], "cannot_loan_" + state)
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_all_other_roles_receive_403_for_loan_and_return(self):
        for role in User.Role.values:
            if role != User.Role.MUSEOLOGO:
                with self.subTest(role=role):
                    self.user.role = role
                    self.user.save()
                    self.assertEqual(self.client.post(self.loan_url, self.payload, format="json").status_code, 403)
                    self.assertEqual(self.client.post(self.return_url, {}, format="json").status_code, 403)

    def test_loan_and_return_roll_back_if_audit_fails(self):
        with patch("collection_integrity.services.record", side_effect=RuntimeError("Audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.loan_url, self.payload, format="json")
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.location), ("displayed", "Room 1"))
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())
        self.client.post(self.loan_url, self.payload, format="json")
        with patch("collection_integrity.services.record", side_effect=RuntimeError("Audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.return_url, {}, format="json")
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.loan_to), ("loaned", "Museum B"))
        self.assertEqual(AuditEntry.objects.filter(entity="piece").count(), 1)

    def test_duplicate_loan_or_return_is_rejected(self):
        self.assertEqual(self.client.post(self.return_url, {}, format="json").status_code, 400)
        self.client.post(self.loan_url, self.payload, format="json")
        self.assertEqual(self.client.post(self.loan_url, self.payload, format="json").status_code, 400)
        self.client.post(self.return_url, {}, format="json")
        self.assertEqual(self.client.post(self.return_url, {}, format="json").status_code, 400)
        self.assertEqual(AuditEntry.objects.filter(entity="piece").count(), 2)

    def test_generic_edit_cannot_bypass_loan_or_return(self):
        self.assertEqual(self.client.patch(self.detail_url, {"state": "loaned"}, format="json").status_code, 400)
        self.client.post(self.loan_url, self.payload, format="json")
        for payload in [{"state": "stored"}, {"location": "Room 2"}, {"loan_to": "Override"}, {"loan_start": "2025-01-01"}, {"loan_end": "2025-01-02"}]:
            self.assertEqual(self.client.patch(self.detail_url, payload, format="json").status_code, 400)
        self.assertEqual(self.client.patch(self.detail_url, {"title": "Corrected"}, format="json").status_code, 200)
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.title), ("loaned", "Corrected"))

    def test_service_enforces_role_and_period(self):
        self.user.role = User.Role.ADMINISTRADOR_GENERAL
        with self.assertRaises(PermissionDenied):
            loan_piece(user=self.user, piece_id=self.piece.pk, **self.payload)
        with self.assertRaises(PermissionDenied):
            return_piece(user=self.user, piece_id=self.piece.pk)
        self.user.role = User.Role.MUSEOLOGO
        with self.assertRaises(ValidationError):
            loan_piece(user=self.user, piece_id=self.piece.pk, **(self.payload | {"end_date": "2025-12-31"}))

    def test_list_filter_and_subsequent_loan_preserve_previous_history(self):
        self.client.post(self.loan_url, self.payload, format="json")
        self.assertEqual(self.client.get("/api/pieces/?state=loaned").json()[0]["id"], self.piece.pk)
        self.assertEqual(self.client.get("/api/pieces/?state=displayed").json(), [])
        self.client.post(self.return_url, {}, format="json")
        self.client.post(self.loan_url, self.payload | {"recipient": "Museum C"}, format="json")
        self.assertEqual(AuditEntry.objects.filter(entity="piece").count(), 3)
        original = AuditEntry.objects.filter(entity="piece").earliest("pk")
        self.assertEqual(original.changes["loan_to"]["new"], "Museum B")
