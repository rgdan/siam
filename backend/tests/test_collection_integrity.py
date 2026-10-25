from unittest.mock import patch

from api.models import User
from audit.models import AuditEntry
from collection_integrity.models import Photo, Piece, PieceHistory
from collection_integrity.services import (
    change_piece_state,
    decommission_piece,
    edit_piece,
    loan_piece,
    register_piece,
)
from django.test import TestCase


class CollectionIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="museo@test.cr", full_name="Museologist", role="museologo"
        )

    def test_exception_halfway_registration_leaves_no_rows(self):
        original = Photo.objects.create
        calls = 0

        def fail_second(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("Forced failure after piece and first photo")
            return original(**kwargs)

        with patch.object(Photo.objects, "create", side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                register_piece(
                    user=self.user,
                    title="Interrupted",
                    photos=[
                        {"name": "first", "content": b"first"},
                        {"name": "second", "content": b"second"},
                    ],
                )
        self.assertEqual(calls, 2)
        self.assertEqual(
            [m.objects.count() for m in (Piece, Photo, PieceHistory, AuditEntry)],
            [0, 0, 0, 0],
        )

    def test_each_operation_logs_once_and_keeps_history(self):
        piece = register_piece(
            user=self.user,
            title="Original",
            photos=[{"name": "p", "content": b"photo"}],
        )
        edit_piece(
            user=self.user,
            piece_id=piece.pk,
            title="Edited",
            photos=[{"name": "new", "content": b"new"}],
        )
        entry = AuditEntry.objects.first()
        self.assertEqual(entry.changes["title"], {"old": "Original", "new": "Edited"})
        loan_piece(user=self.user, piece_id=piece.pk, recipient="Other museum")
        change_piece_state(user=self.user, piece_id=piece.pk, state="stored")
        decommission_piece(user=self.user, piece_id=piece.pk)
        self.assertEqual(AuditEntry.objects.count(), 5)
        self.assertEqual(PieceHistory.objects.count(), 5)
        self.assertEqual(Photo.objects.get().name, "new")
        self.assertEqual(AuditEntry.objects.first().action_type, "decommission")

    def test_every_operation_rolls_back_on_history_failure(self):
        piece = register_piece(
            user=self.user,
            title="Original",
            photos=[{"name": "p", "content": b"photo"}],
        )
        operations = [
            lambda: edit_piece(
                user=self.user, piece_id=piece.pk, title="Changed", photos=[]
            ),
            lambda: loan_piece(user=self.user, piece_id=piece.pk, recipient="Other"),
            lambda: change_piece_state(
                user=self.user, piece_id=piece.pk, state="stored"
            ),
            lambda: decommission_piece(user=self.user, piece_id=piece.pk),
        ]
        for operation in operations:
            with self.subTest(operation=operation):
                with patch.object(
                    PieceHistory.objects,
                    "create",
                    side_effect=RuntimeError("history failed"),
                ):
                    with self.assertRaises(RuntimeError):
                        operation()
                piece.refresh_from_db()
                self.assertEqual(
                    (piece.title, piece.state, piece.loan_to, piece.decommissioned),
                    ("Original", "registered", "", False),
                )
                self.assertEqual(Photo.objects.count(), 1)
                self.assertEqual(AuditEntry.objects.count(), 1)
                self.assertEqual(PieceHistory.objects.count(), 1)

    def test_register_rolls_back_even_after_audit(self):
        with patch.object(
            PieceHistory.objects, "create", side_effect=RuntimeError("history failed")
        ):
            with self.assertRaises(RuntimeError):
                register_piece(
                    user=self.user,
                    title="Piece",
                    photos=[{"name": "p", "content": b"p"}],
                )
        self.assertEqual(
            [m.objects.count() for m in (Piece, Photo, PieceHistory, AuditEntry)],
            [0, 0, 0, 0],
        )
