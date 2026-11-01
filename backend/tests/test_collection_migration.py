from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CollectionMigrationTests(TransactionTestCase):
    def test_legacy_pieces_get_distinct_identifiers_and_preserve_data(self):
        before = [("collection_integrity", "0001_initial")]
        after = [
            (
                "collection_integrity",
                "0003_alter_piece_state_piece_piece_valid_state_and_more",
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
