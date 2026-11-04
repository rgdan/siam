from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from api.models import User
from audit.models import AuditEntry
from .models import Photo, Piece
from .services import mark_missing


class MissingPieceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="museum@example.com", full_name="Museum", role=User.Role.MUSEOLOGO,
        )
        self.piece = Piece.objects.create(title="Original", state="displayed", location="Room 1")
        self.photo = Photo.objects.create(piece=self.piece, name="Original photo", content=b"original")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f"/api/pieces/{self.piece.pk}/missing/"
        self.detail_url = f"/api/pieces/{self.piece.pk}/"
        self.payload = {"state": "stolen", "event_date": str(timezone.localdate()), "confirmed": True}

    def test_both_states_from_storage_or_display_preserve_data_and_audit(self):
        for previous in ["stored", "displayed"]:
            for chosen in ["stolen", "lost"]:
                with self.subTest(previous=previous, chosen=chosen):
                    piece = Piece.objects.create(
                        title="Original", state=previous, location="Room 1" if previous == "displayed" else "",
                    )
                    Photo.objects.create(piece=piece, name="Original", content=b"original")
                    historical = AuditEntry.objects.create(
                        user=self.user, role=self.user.role, action_type="create", entity="piece",
                        entity_id=str(piece.pk), changes={"title": {"old": None, "new": "Original"}},
                    )
                    response = self.client.post(
                        f"/api/pieces/{piece.pk}/missing/", self.payload | {"state": chosen, "observations": "Event details"}, format="json",
                    )
                    self.assertEqual(response.status_code, 200)
                    piece.refresh_from_db()
                    self.assertEqual((piece.state, piece.location, piece.title), (chosen, "", "Original"))
                    self.assertEqual(piece.event_date, timezone.localdate())
                    self.assertEqual(piece.event_observations, "Event details")
                    self.assertEqual(piece.photos.get().content, b"original")
                    detail = self.client.get(f"/api/pieces/{piece.pk}/").json()
                    self.assertEqual(len(detail["history"]), 2)
                    self.assertEqual(detail["history"][0]["user"], self.user.full_name)
                    self.assertIsNotNone(detail["history"][0]["timestamp"])
                    self.assertEqual(detail["history"][0]["changes"]["state"], {"old": previous, "new": chosen})
                    historical.refresh_from_db()
                    self.assertEqual(historical.changes["title"]["new"], "Original")

    def test_invalid_or_missing_fields_do_not_change_piece(self):
        cases = [
            self.payload | {"state": state} for state in ["stored", "displayed", "decommissioned", "", ["stolen", "lost"]]
        ] + [
            self.payload | {"event_date": date} for date in ["", "invalid", None, str(timezone.localdate() + timedelta(days=1))]
        ] + [self.payload | {"confirmed": False}]
        cases += [{key: value for key, value in self.payload.items() if key != field} for field in self.payload]
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 400)
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.location), ("displayed", "Room 1"))
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_optional_observations_and_past_date(self):
        response = self.client.post(
            self.url, self.payload | {"event_date": str(timezone.localdate() - timedelta(days=1))}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["event_observations"], "")

    def test_decommissioned_piece_cannot_be_marked_missing(self):
        self.piece.decommissioned = True
        self.piece.save()
        for state in ["stolen", "lost"]:
            self.assertEqual(self.client.post(self.url, self.payload | {"state": state}, format="json").status_code, 400)
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "displayed")
        self.assertTrue(self.piece.decommissioned)
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_all_other_roles_denied_including_administrators(self):
        for role in User.Role.values:
            if role == User.Role.MUSEOLOGO:
                continue
            with self.subTest(role=role):
                self.user.role = role
                self.user.save()
                self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 403)
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "displayed")

    def test_audit_failure_rolls_back_entire_change(self):
        with patch("collection_integrity.services.record", side_effect=RuntimeError("Audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url, self.payload, format="json")
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.location, self.piece.event_date), ("displayed", "Room 1", None))
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_state_cannot_be_bypassed_using_generic_piece_endpoints(self):
        for state in ["stolen", "lost"]:
            self.assertEqual(self.client.patch(self.detail_url, {"state": state}, format="json").status_code, 400)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 200)
        for payload in [{"state": "stored"}, {"location": "Room 2"}, {"event_date": "2000-01-01"}, {"event_observations": "Override"}]:
            self.assertEqual(self.client.patch(self.detail_url, payload, format="json").status_code, 400)
        self.assertEqual(self.client.patch(self.detail_url, {"title": "Corrected"}, format="json").status_code, 200)
        self.piece.refresh_from_db()
        self.assertEqual((self.piece.state, self.piece.title), ("stolen", "Corrected"))

    def test_list_filters_and_detail_show_new_states(self):
        for state in ["stolen", "lost"]:
            self.assertEqual(self.client.post(self.url, self.payload | {"state": state}, format="json").status_code, 200)
            self.assertEqual(self.client.get(self.detail_url).json()["state"], state)
            self.assertEqual(self.client.get(f"/api/pieces/?state={state}").json()[0]["id"], self.piece.pk)
            for previous in ["stored", "displayed"]:
                self.assertEqual(self.client.get(f"/api/pieces/?state={previous}").json(), [])

    def test_service_enforces_role_and_future_date(self):
        self.user.role = User.Role.ADMINISTRADOR_GENERAL
        with self.assertRaises(PermissionDenied):
            mark_missing(user=self.user, piece_id=self.piece.pk, **self.payload)
        self.user.role = User.Role.MUSEOLOGO
        with self.assertRaises(ValidationError):
            mark_missing(user=self.user, piece_id=self.piece.pk, **(self.payload | {"event_date": str(timezone.localdate() + timedelta(days=1))}))


    def test_recovery_restores_storage_preserves_piece_and_records_audit(self):
        for state in ["stolen", "lost"]:
            with self.subTest(state=state):
                self.assertEqual(self.client.post(self.url, self.payload | {"state": state}, format="json").status_code, 200)
                response = self.client.post(f"/api/pieces/{self.piece.pk}/recover/", {}, format="json")
                self.assertEqual(response.status_code, 200)
                self.piece.refresh_from_db()
                self.assertEqual((self.piece.state, self.piece.location, self.piece.title), ("stored", "", "Original"))
                self.assertIsNone(self.piece.event_date)
                self.assertEqual(self.piece.event_observations, "")
                self.assertEqual(self.piece.photos.get().content, b"original")
                entry = AuditEntry.objects.filter(entity="piece", entity_id=str(self.piece.pk)).latest("timestamp")
                self.assertEqual(entry.changes["state"], {"old": state, "new": "stored"})
                self.assertEqual(entry.user, self.user)
                self.assertTrue(AuditEntry.objects.filter(entity="piece", changes__state__new=state).exists())

    def test_recovery_rejects_other_states_and_decommissioned_pieces(self):
        for state in ["stored", "displayed", "loaned", "decommissioned"]:
            with self.subTest(state=state):
                Piece.objects.filter(pk=self.piece.pk).update(state=state, location="Room 1" if state == "displayed" else "")
                self.assertEqual(self.client.post(f"/api/pieces/{self.piece.pk}/recover/", {}, format="json").status_code, 400)
                self.piece.refresh_from_db()
                self.assertEqual(self.piece.state, state)
        Piece.objects.filter(pk=self.piece.pk).update(state="stolen", location="", decommissioned=True)
        self.assertEqual(self.client.post(f"/api/pieces/{self.piece.pk}/recover/", {}, format="json").status_code, 400)
        self.assertFalse(AuditEntry.objects.filter(entity="piece").exists())

    def test_recovery_denies_other_roles_and_unknown_piece(self):
        Piece.objects.filter(pk=self.piece.pk).update(state="stolen", location="")
        for role in User.Role.values:
            if role == User.Role.MUSEOLOGO:
                continue
            self.user.role = role
            self.user.save()
            self.assertEqual(self.client.post(f"/api/pieces/{self.piece.pk}/recover/", {}, format="json").status_code, 403)
        self.user.role = User.Role.MUSEOLOGO
        self.user.save()
        self.assertEqual(self.client.post("/api/pieces/999999/recover/", {}, format="json").status_code, 404)
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "stolen")

    def test_recovery_audit_failure_rolls_back(self):
        self.client.post(self.url, self.payload, format="json")
        with patch("collection_integrity.services.record", side_effect=RuntimeError("Audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.post(f"/api/pieces/{self.piece.pk}/recover/", {}, format="json")
        self.piece.refresh_from_db()
        self.assertEqual(self.piece.state, "stolen")
        self.assertEqual(self.piece.event_date, timezone.localdate())

    def test_recovery_service_enforces_role(self):
        from .services import recover_piece
        self.user.role = User.Role.ADMINISTRADOR_GENERAL
        with self.assertRaises(PermissionDenied):
            recover_piece(user=self.user, piece_id=self.piece.pk)
