import json
import re
import unicodedata

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from .models import AuditEntry


def _secret(key):
    key = (
        unicodedata.normalize("NFKD", str(key))
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    key = re.sub(r"[^a-z0-9]", "", key)
    return any(
        part in key for part in ("password", "passwd", "contrasena", "token", "secret")
    )


def sanitize(value):
    if isinstance(value, dict):
        return {str(k): sanitize(v) for k, v in value.items() if not _secret(k)}
    if isinstance(value, (list, tuple)):
        return [sanitize(v) for v in value]
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


def snapshot(instance):

    return sanitize(
        {
            f.name: getattr(instance, f.attname)
            for f in instance._meta.concrete_fields
            if f.get_internal_type() != "BinaryField" and not _secret(f.name)
        }
    )


def record(*, user, action_type, entity, entity_id="", old=None, new=None):

    if action_type not in AuditEntry.Action.values:
        raise ValueError("Tipo de acción desconocido.")
    before, after = sanitize(old or {}), sanitize(new or {})
    changes = {
        key: {"old": before.get(key), "new": after.get(key)}
        for key in before.keys() | after.keys()
        if before.get(key) != after.get(key)
    }
    actor = user if user is not None and user.is_authenticated else None
    return AuditEntry.objects.create(
        user=actor,
        role=getattr(actor, "role", ""),
        action_type=action_type,
        entity=entity,
        entity_id=str(entity_id),
        changes=changes,
    )


@transaction.atomic
def audited_create(*, user, entity, create):

    instance = create()
    record(
        user=user,
        action_type=AuditEntry.Action.CREATE,
        entity=entity,
        entity_id=instance.pk,
        new=snapshot(instance),
    )
    return instance
