from contextlib import contextmanager

from audit.models import AuditEntry
from audit.services import record, snapshot
from django.db import transaction

from .models import Photo, Piece


@contextmanager
def collection_transaction():

    with transaction.atomic():
        yield


def _finish(piece, user, operation, old):
    new = snapshot(piece)
    action = {
        "register": AuditEntry.Action.CREATE,
        "decommission": AuditEntry.Action.DECOMMISSION,
    }.get(operation, AuditEntry.Action.MODIFY)
    record(
        user=user,
        action_type=action,
        entity="piece",
        entity_id=piece.pk,
        old=old,
        new=new,
    )


def register_piece(*, user, title, photos=(), **fields):
    with collection_transaction():
        piece = Piece(title=title, **fields)
        piece.full_clean()
        piece.save()
        for photo in photos:
            Photo.objects.create(piece=piece, **photo)
        _finish(piece, user, "register", {})
        return piece


def _change(*, user, piece_id, operation, values, photos=None):
    with collection_transaction():
        piece = Piece.objects.select_for_update().get(pk=piece_id)
        old = snapshot(piece)
        old["photos"] = list(piece.photos.values_list("pk", flat=True))
        for key, value in values.items():
            setattr(piece, key, value)
        piece.full_clean()
        piece.save()
        if photos is not None:
            piece.photos.all().delete()
            for photo in photos:
                Photo.objects.create(piece=piece, **photo)
        new = snapshot(piece)
        new["photos"] = list(piece.photos.values_list("pk", flat=True))
        action = (
            AuditEntry.Action.DECOMMISSION
            if operation == "decommission"
            else AuditEntry.Action.MODIFY
        )
        record(
            user=user,
            action_type=action,
            entity="piece",
            entity_id=piece.pk,
            old=old,
            new=new,
        )
        return piece


def edit_piece(*, user, piece_id, title, photos=None):
    return _change(
        user=user,
        piece_id=piece_id,
        operation="edit",
        values={"title": title},
        photos=photos,
    )


def decommission_piece(*, user, piece_id):
    return _change(
        user=user,
        piece_id=piece_id,
        operation="decommission",
        values={"decommissioned": True},
    )


def loan_piece(*, user, piece_id, recipient):
    if not recipient.strip():
        raise ValueError("El destinatario es obligatorio.")
    return _change(
        user=user,
        piece_id=piece_id,
        operation="loan",
        values={"loan_to": recipient},
    )


def change_piece_state(*, user, piece_id, state, location=""):
    return _change(
        user=user,
        piece_id=piece_id,
        operation="state",
        values={"state": state, "location": location if state == "displayed" else ""},
    )


@transaction.atomic
def attach_photo(*, user, piece_id, values):
    piece = Piece.objects.select_for_update().get(pk=piece_id)
    old = snapshot(piece)
    old["photos"] = list(piece.photos.values_list("pk", flat=True))
    photo = Photo.objects.create(piece=piece, **values)
    new = snapshot(piece)
    new["photos"] = list(piece.photos.values_list("pk", flat=True))
    record(
        user=user,
        action_type=AuditEntry.Action.MODIFY,
        entity="piece",
        entity_id=piece.pk,
        old=old,
        new=new,
    )
    return photo
