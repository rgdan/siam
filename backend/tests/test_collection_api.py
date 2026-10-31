import base64
from io import BytesIO
from unittest.mock import patch

from api.models import User
from audit.models import AuditEntry
from collection_integrity.models import Photo, Piece, PieceHistory
from collection_integrity.serializers import OBJECT_FIELDS
from django.db import IntegrityError, transaction
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient


class CollectionAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.curator = User.objects.create_user(
            email="curator@example.com", full_name="Curator", role="museologo"
        )
        cls.payload = {field: "Description" for field in OBJECT_FIELDS}
        cls.payload.update(
            title="Vase", measurement_value="12.5", measurement_unit="cm"
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.curator)

    def create_piece(self):
        response = self.client.post("/api/pieces/", self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def update(self, piece, values):
        return self.client.patch(f"/api/pieces/{piece['id']}/", values, format="json")

    def image(self, name="vase.png", fmt="PNG"):
        stream = BytesIO()
        Image.new("RGB", (4, 4), "red").save(stream, format=fmt)
        return {"name": name, "content": base64.b64encode(stream.getvalue()).decode()}

    def upload(self, piece, files):
        return self.client.post(
            f"/api/pieces/{piece['id']}/photos/", {"photos": files}, format="json"
        )

    def test_registration_identifier_storage_list_and_one_audit(self):
        first, second = self.create_piece(), self.create_piece()
        self.assertNotEqual(first["identifier"], second["identifier"])
        self.assertEqual(first["state"], "stored")
        self.assertEqual(first["location"], "")
        self.assertEqual(AuditEntry.objects.filter(action_type="create").count(), 2)
        self.assertEqual(len(self.client.get("/api/pieces/").data), 2)
        self.assertEqual(
            self.client.get(f"/api/pieces/{first['id']}/").data["photos"], []
        )

    def test_all_required_fields_reported_and_no_rows(self):
        response = self.client.post("/api/pieces/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data), set(OBJECT_FIELDS))
        self.assertFalse(Piece.objects.exists())
        self.assertFalse(AuditEntry.objects.exists())

    def test_invalid_measurements_and_unit(self):
        for value in ["12 cm", "zero", "0", "-2", "NaN", "Infinity", "1.12345"]:
            with self.subTest(value=value):
                response = self.client.post(
                    "/api/pieces/",
                    {**self.payload, "measurement_value": value},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("measurement_value", response.data)
        response = self.client.post(
            "/api/pieces/",
            {**self.payload, "measurement_unit": "injected"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Piece.objects.exists())

    def test_only_exact_curator_role_can_use_every_endpoint(self):
        piece = self.create_piece()
        for role in [
            "guarda",
            "coordinador",
            "administrador_general",
            "administrador_sistema",
        ]:
            user = User.objects.create_user(
                email=f"{role}@example.com", full_name=role, role=role
            )
            self.client.force_authenticate(user)
            for response in [
                self.client.post("/api/pieces/", self.payload, format="json"),
                self.update(piece, {"title": "Denied"}),
                self.upload(piece, [self.image()]),
                self.client.get("/api/pieces/"),
            ]:
                self.assertEqual(response.status_code, 403, (role, response.data))
        self.assertEqual(Piece.objects.get().title, "Vase")
        self.assertFalse(Photo.objects.exists())

    def test_unauthenticated_gets_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/pieces/").status_code, 401)

    def test_identifier_is_rejected_and_never_changes(self):
        piece = self.create_piece()
        response = self.update(
            piece,
            {"identifier": "00000000-0000-0000-0000-000000000000", "title": "Invalid"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(Piece.objects.get().identifier), piece["identifier"])
        self.assertEqual(Piece.objects.get().title, "Vase")

    def test_display_requires_location_and_state_filter_is_exact(self):
        piece = self.create_piece()
        for location in ["", "  ", "x" * 201]:
            response = self.update(piece, {"state": "displayed", "location": location})
            self.assertEqual(response.status_code, 400)
            self.assertIn("location", response.data)
        self.assertEqual(self.update(piece, {"state": "other"}).status_code, 400)
        self.assertEqual(
            self.update(
                piece, {"state": "displayed", "location": "Room A, case 2"}
            ).status_code,
            200,
        )
        self.create_piece()
        displayed = self.client.get("/api/pieces/?state=displayed").data
        stored = self.client.get("/api/pieces/?state=stored").data
        self.assertEqual([p["id"] for p in displayed], [piece["id"]])
        self.assertEqual(displayed[0]["location"], "Room A, case 2")
        self.assertEqual(len(stored), 1)

    def test_location_only_change_and_storage_keep_history(self):
        piece = self.create_piece()
        self.update(piece, {"state": "displayed", "location": "Room A"})
        changed = self.update(piece, {"location": "Room B"})
        self.assertEqual(changed.data["state"], "displayed")
        self.assertEqual(
            changed.data["history"][0]["changes"]["location"],
            {"old": "Room A", "new": "Room B"},
        )
        response = self.update(piece, {"state": "stored"})
        self.assertEqual(response.data["location"], "")
        history = response.data["history"][0]
        self.assertEqual(history["user"], self.curator.email)
        self.assertTrue(history["timestamp"])
        self.assertEqual(history["changes"]["location"], {"old": "Room B", "new": ""})
        self.assertEqual(
            history["changes"]["state"], {"old": "displayed", "new": "stored"}
        )
        self.assertEqual(self.update(piece, {"state": "displayed"}).status_code, 400)

    def test_every_object_field_updates_and_is_recorded(self):
        piece = self.create_piece()
        changes = {
            **self.payload,
            "title": "Updated",
            "measurement_value": "42.0000",
            "measurement_unit": "kg",
        }
        for field in OBJECT_FIELDS:
            if field not in ["title", "measurement_value", "measurement_unit"]:
                changes[field] = "Updated " + field
        response = self.update(piece, changes)
        self.assertEqual(response.status_code, 200, response.data)
        history = response.data["history"][0]
        self.assertEqual(set(history["changes"]), set(OBJECT_FIELDS))
        self.assertEqual(self.client.get("/api/pieces/").data[0]["title"], "Updated")
        self.assertEqual(response.data["identifier"], piece["identifier"])

    def test_invalid_edit_and_inactive_piece_keep_original(self):
        piece = self.create_piece()
        self.assertEqual(
            self.update(piece, {"title": "", "subject": "Altered"}).status_code, 400
        )
        self.assertEqual(Piece.objects.get().subject, self.payload["subject"])
        Piece.objects.update(decommissioned=True)
        self.assertEqual(self.update(piece, {"title": "Altered"}).status_code, 400)
        self.assertEqual(Piece.objects.get().title, "Vase")

    def test_noop_does_not_add_history(self):
        piece = self.create_piece()
        self.assertEqual(self.update(piece, {"title": "Vase"}).status_code, 200)
        self.assertEqual(PieceHistory.objects.count(), 1)

    def test_atomic_creation_and_edit_when_history_fails(self):
        with (
            patch.object(
                PieceHistory.objects, "create", side_effect=RuntimeError("history")
            ),
            self.assertRaises(RuntimeError),
        ):
            self.create_piece()
        self.assertFalse(Piece.objects.exists())
        self.assertFalse(AuditEntry.objects.exists())
        piece = self.create_piece()
        with (
            patch.object(
                PieceHistory.objects, "create", side_effect=RuntimeError("history")
            ),
            self.assertRaises(RuntimeError),
        ):
            self.update(piece, {"title": "Altered", "subject": "Altered"})
        saved = Piece.objects.get()
        self.assertEqual(saved.title, "Vase")
        self.assertEqual(saved.subject, self.payload["subject"])
        self.assertEqual(AuditEntry.objects.count(), 1)

    def test_multi_photo_partial_rejections_and_later_append(self):
        piece = self.create_piece()
        bad = {
            "name": "fake.png",
            "content": base64.b64encode(b"not an image").decode(),
        }
        large = {
            "name": "large.png",
            "content": base64.b64encode(b"x" * (5 * 1024 * 1024 + 1)).decode(),
        }
        response = self.upload(
            piece,
            [
                self.image(),
                bad,
                self.image("bad.gif", "GIF"),
                large,
                self.image("second.png"),
            ],
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            ["id" in row for row in response.data["results"]],
            [True, False, False, False, True],
        )
        self.assertIn("too_large", str(response.data["results"][3]))
        self.assertIn("invalid_format", str(response.data["results"][2]))
        self.upload(piece, [self.image("third.png")])
        detail = self.client.get(f"/api/pieces/{piece['id']}/").data
        self.assertEqual(len(detail["photos"]), 3)
        self.assertTrue(
            detail["photos"][0]["data"].startswith("data:image/png;base64,")
        )

    def test_failed_photo_transaction_preserves_previous_and_other_uploads(self):
        piece = self.create_piece()
        self.upload(piece, [self.image("existing.png")])
        original = PieceHistory.objects.create
        calls = 0

        def fail_once(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("history failed")
            return original(**kwargs)

        with (
            patch.object(PieceHistory.objects, "create", side_effect=fail_once),
            self.assertLogs("collection_integrity.views", level="ERROR"),
        ):
            response = self.upload(
                piece, [self.image("failed.png"), self.image("success.png")]
            )
        self.assertIn("errors", response.data["results"][0])
        self.assertIn("id", response.data["results"][1])
        self.assertEqual(
            set(Photo.objects.values_list("name", flat=True)),
            {"existing.png", "success.png"},
        )
        self.assertEqual(Piece.objects.get().title, "Vase")
        self.assertEqual(PieceHistory.objects.count(), 3)
        self.assertEqual(AuditEntry.objects.count(), 3)

    def test_database_rejects_invalid_state_or_current_location(self):
        piece = self.create_piece()
        for values in [
            {"state": "invalid"},
            {"state": "displayed", "location": ""},
            {"state": "stored", "location": "Not current"},
        ]:
            with (
                self.subTest(values=values),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                Piece.objects.filter(pk=piece["id"]).update(**values)
