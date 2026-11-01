from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class CollectionMigrationTests(TransactionTestCase):
    def test_legacy_pieces_get_distinct_identifiers_and_preserve_data(self):
        before = [("collection_integrity", "0001_initial")]
        after = [
            (
                "collection_integrity",
                "0004_move_history_to_audit",
            )
        ]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            Piece = apps.get_model("collection_integrity", "Piece")
            Photo = apps.get_model("collection_integrity", "Photo")
            first = Piece.objects.create(title="Existing", state="registered")
            second = Piece.objects.create(
                title="Loan", state="loaned", loan_to="Museum"
            )
            third = Piece.objects.create(
                title="Display without location", state="displayed"
            )
            Photo.objects.create(piece=first, name="existing.jpg", content=b"original")
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            Piece = apps.get_model("collection_integrity", "Piece")
            Photo = apps.get_model("collection_integrity", "Photo")
            self.assertEqual(
                len(set(Piece.objects.values_list("identifier", flat=True))), 3
            )
            self.assertEqual(
                set(Piece.objects.values_list("state", flat=True)), {"stored"}
            )
            self.assertEqual(Piece.objects.get(pk=second.pk).loan_to, "Museum")
            self.assertEqual(
                Piece.objects.get(pk=third.pk).title, "Display without location"
            )
            self.assertEqual(bytes(Photo.objects.get().content), b"original")
        finally:
            MigrationExecutor(connection).migrate(after)

    def test_history_moves_to_audit_without_duplicates_or_data_loss(self):
        before = [
            ("collection_integrity", "0003_alter_piece_state_piece_piece_valid_state_and_more"),
            ("audit", "0001_initial"),
        ]
        after = [("collection_integrity", "0004_move_history_to_audit")]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            User = apps.get_model("api", "User")
            Piece = apps.get_model("collection_integrity", "Piece")
            Photo = apps.get_model("collection_integrity", "Photo")
            History = apps.get_model("collection_integrity", "PieceHistory")
            Audit = apps.get_model("audit", "AuditEntry")
            user = User.objects.create(email="legacy@test.cr", role="museologo")
            piece = Piece.objects.create(title="Preserved", state="stored")
            Photo.objects.create(piece=piece, name="photo.png", content=b"original")
            changes = {"title": {"old": "Before", "new": "Preserved"}}
            existing = Audit.objects.create(
                user=user, role="museologo", entity="piece", entity_id=str(piece.pk),
                action_type="modify", changes=changes,
            )
            original_timestamp = existing.timestamp
            unrelated = Audit.objects.create(entity="user", action_type="modify")
            legacy_time = timezone.now() - timedelta(days=30)
            for operation in ("edit", "edit", "register", "decommission"):
                history = History.objects.create(
                    user=user, piece=piece, operation=operation, changes=changes,
                )
                History.objects.filter(pk=history.pk).update(timestamp=legacy_time)

            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            Audit = apps.get_model("audit", "AuditEntry")
            entries = Audit.objects.filter(entity="piece", entity_id=str(piece.pk))
            self.assertEqual(entries.count(), 4)
            self.assertEqual(
                sorted(entries.values_list("action_type", flat=True)),
                ["create", "decommission", "modify", "modify"],
            )
            existing.refresh_from_db()
            self.assertEqual(existing.timestamp, original_timestamp)
            self.assertEqual(existing.changes, changes)
            self.assertTrue(Audit.objects.filter(pk=unrelated.pk, entity="user").exists())
            for entry in entries.exclude(pk=existing.pk):
                self.assertEqual(entry.timestamp, legacy_time)
                self.assertEqual((entry.user_id, entry.role), (user.pk, "museologo"))
                self.assertEqual(entry.changes, changes)
            migrated_piece = apps.get_model("collection_integrity", "Piece").objects.get()
            self.assertEqual(migrated_piece.identifier, piece.identifier)
            self.assertEqual(migrated_piece.title, "Preserved")
            self.assertEqual(
                bytes(apps.get_model("collection_integrity", "Photo").objects.get().content),
                b"original",
            )
            self.assertNotIn("collection_integrity_piecehistory", connection.introspection.table_names())
        finally:
            MigrationExecutor(connection).migrate(after)
