import json
from collections import Counter

from django.db import migrations


def move_history_to_audit(apps, schema_editor):
    History = apps.get_model("collection_integrity", "PieceHistory")
    Audit = apps.get_model("audit", "AuditEntry")
    database = schema_editor.connection.alias

    def key(user_id, piece_id, action, changes):
        return user_id, str(piece_id), action, json.dumps(changes, sort_keys=True)

    # Consume matching entries once so repeated identical operations survive.
    existing = Counter(
        key(entry.user_id, entry.entity_id, entry.action_type, entry.changes)
        for entry in Audit.objects.using(database).filter(entity="piece").iterator()
    )
    for history in (
        History.objects.using(database)
        .select_related("user")
        .order_by("timestamp", "pk")
        .iterator()
    ):
        action = {"register": "create", "decommission": "decommission"}.get(
            history.operation, "modify"
        )
        identity = key(history.user_id, history.piece_id, action, history.changes)
        if existing[identity]:
            existing[identity] -= 1
            continue
        entry = Audit.objects.using(database).create(
            user_id=history.user_id,
            role=history.user.role,
            action_type=action,
            entity="piece",
            entity_id=str(history.piece_id),
            changes=history.changes,
        )
        Audit.objects.using(database).filter(pk=entry.pk).update(
            timestamp=history.timestamp
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "collection_integrity",
            "0003_alter_piece_state_piece_piece_valid_state_and_more",
        ),
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(move_history_to_audit, migrations.RunPython.noop),
        migrations.DeleteModel(name="PieceHistory"),
    ]
