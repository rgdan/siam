from contextlib import contextmanager

from audit.models import AuditEntry
from audit.services import record, snapshot
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from api.models import User

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
        for position, photo in enumerate(photos):
            Photo.objects.create(piece=piece, position=position, **photo)
        _finish(piece, user, "register", {})
        return piece


def _change(*, user, piece_id, operation, values, photos=None):
    with collection_transaction():
        piece = Piece.objects.select_for_update().get(pk=piece_id)
        if operation in ["loan", "return"] and piece.decommissioned:
            raise ValidationError({"detail": "cannot_loan_decommissioned"})
        if piece.decommissioned:
            raise ValidationError({"detail": "inactive_piece"})
        if operation == "loan" and piece.state not in ["stored", "displayed"]:
            raise ValidationError({"detail": "cannot_loan_" + piece.state})
        if operation == "return" and piece.state != "loaned":
            raise ValidationError({"detail": "not_loaned"})
        if operation == "state" and (piece.state not in ["stored", "displayed"] or values["state"] not in ["stored", "displayed"]):
            raise ValidationError({"detail": "unavailable_piece"})
        if operation == "recover" and piece.state not in ["stolen", "lost"]:
            raise ValidationError({"detail": "not_missing"})
        old = snapshot(piece)
        old["photos"] = list(piece.photos.values_list("pk", flat=True))
        for key, value in values.items():
            setattr(piece, key, value)
        piece.full_clean()
        piece.save()
        if photos is not None:
            piece.photos.all().delete()
            for position, photo in enumerate(photos):
                Photo.objects.create(piece=piece, position=position, **photo)
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


def require_museologist(user):
    if not user.is_active or user.role != User.Role.MUSEOLOGO:
        raise PermissionDenied("museologist_only")


def decommission_piece(*, user, piece_id, reason, confirmed):
    require_museologist(user)
    if not confirmed or not reason.strip():
        raise ValidationError({"detail": "confirmation_and_reason_required"})
    return _change(
        user=user, piece_id=piece_id, operation="decommission",
        values={"state": "decommissioned", "location": "", "decommissioned": True,
                "decommissioned_at": timezone.now(), "decommission_reason": reason.strip(),
                "decommissioned_by": user},
    )


def loan_piece(*, user, piece_id, recipient, start_date, end_date):
    from .serializers import LoanSerializer

    require_museologist(user)
    serializer = LoanSerializer(data={"recipient": recipient, "start_date": start_date, "end_date": end_date})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    return _change(
        user=user,
        piece_id=piece_id,
        operation="loan",
        values={"state": "loaned", "location": "", "loan_to": data["recipient"],
                "loan_start": data["start_date"], "loan_end": data["end_date"]},
    )


def return_piece(*, user, piece_id):
    require_museologist(user)
    return _change(
        user=user, piece_id=piece_id, operation="return",
        values={"state": "stored", "location": "", "loan_to": "", "loan_start": None, "loan_end": None},
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
    if piece.decommissioned:
        raise ValidationError({"detail": "inactive_piece"})
    old = snapshot(piece)
    old["photos"] = list(piece.photos.values_list("pk", flat=True))
    last_position = piece.photos.order_by("-position").values_list("position", flat=True).first()
    photo = Photo.objects.create(
        piece=piece, position=0 if last_position is None else last_position + 1, **values
    )
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


def mark_missing(*, user, piece_id, state, event_date, observations="", confirmed=False):
    from .serializers import MissingPieceSerializer

    require_museologist(user)
    serializer = MissingPieceSerializer(
        data={"state": state, "event_date": event_date,
              "observations": observations, "confirmed": confirmed},
    )
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    return _change(
        user=user, piece_id=piece_id, operation="missing",
        values={"state": data["state"], "event_date": data["event_date"],
                "event_observations": data["observations"], "location": ""},
    )


def recover_piece(*, user, piece_id):
    require_museologist(user)
    return _change(
        user=user, piece_id=piece_id, operation="recover",
        values={"state": "stored", "location": "", "event_date": None,
                "event_observations": "", "loan_to": "", "loan_start": None, "loan_end": None},
    )
