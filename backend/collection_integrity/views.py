import logging

from api.permissions import requiere_permiso
from audit.models import AuditEntry
from audit.services import record, snapshot
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from api.models import User

from .models import Photo, Piece
from .serializers import (
    PhotoOrderSerializer,
    PhotoSerializer,
    PieceSerializer,
    UploadSerializer,
    LoanSerializer,
)
from .services import _finish, attach_photo, register_piece, loan_piece, return_piece, require_museologist
from .reports import collection_report_data

logger = logging.getLogger(__name__)


@api_view(["GET"])
@requiere_permiso("colecciones.generar_reportes")
def collection_report(request):
    if request.user.role != User.Role.MUSEOLOGO:
        raise PermissionDenied("museologist_only")
    return Response(collection_report_data(**{
        key: request.query_params[key]
        for key in ["state", "object_type", "collection"] if key in request.query_params
    }))


@api_view(["GET", "POST"])
@requiere_permiso("piezas.crear")
def pieces(request):
    if request.method == "GET":
        queryset = Piece.objects.order_by("-id")
        state = request.query_params.get("state")
        if state:
            if state not in dict(Piece._meta.get_field("state").choices):
                raise serializers.ValidationError({"state": "invalid_state"})
            queryset = queryset.filter(state=state)
        return Response(PieceSerializer(queryset, many=True).data)
    serializer = PieceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    piece = register_piece(user=request.user, **serializer.validated_data)
    return Response(PieceSerializer(piece).data, status=201)


@api_view(["GET", "PATCH"])
@requiere_permiso("piezas.actualizar")
def piece_detail(request, piece_id):
    with transaction.atomic():
        piece = get_object_or_404(Piece.objects.select_for_update(), pk=piece_id)
        if request.method == "PATCH":
            if piece.decommissioned:
                raise serializers.ValidationError({"detail": "inactive_piece"})
            serializer = PieceSerializer(piece, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            old = snapshot(piece)
            serializer.save()
            if old != snapshot(piece):
                _finish(piece, request.user, "edit", old)
        data = dict(PieceSerializer(piece).data)
        data["history"] = [
            {"id": entry.pk, "timestamp": entry.timestamp, "user": entry.user.full_name if entry.user else None,
             "action": entry.action_type, "changes": entry.changes}
            for entry in AuditEntry.objects.filter(entity="piece", entity_id=str(piece.pk)).select_related("user")
        ]
        data["photos"] = PhotoSerializer(piece.photos.all(), many=True).data
        return Response(data)


@api_view(["POST"])
@requiere_permiso("piezas.adjuntar_fotos")
def upload_photos(request, piece_id):
    piece = get_object_or_404(Piece, pk=piece_id)
    if not isinstance(request.data, dict):
        raise serializers.ValidationError({"photos": "Expected a JSON object."})
    files = request.data.get("photos")
    if not isinstance(files, list) or not 1 <= len(files) <= 20:
        raise serializers.ValidationError({"photos": "Select 1-20 images."})
    results = []
    for index, file in enumerate(files):
        serializer = UploadSerializer(data=file)
        if not serializer.is_valid():
            results.append({"index": index, "errors": serializer.errors})
            continue
        try:
            photo = attach_photo(
                user=request.user, piece_id=piece.pk, values=serializer.validated_data
            )
            results.append({"index": index, "id": photo.pk})
        except Exception:
            logger.exception(
                "Photo upload failed for piece %s, file index %s", piece.pk, index
            )
            results.append(
                {"index": index, "errors": {"non_field_errors": ["upload_failed"]}}
            )
    return Response({"results": results})


@api_view(["DELETE"])
@requiere_permiso("piezas.actualizar")
def delete_photo(request, piece_id, photo_id):
    with transaction.atomic():
        piece = get_object_or_404(Piece.objects.select_for_update(), pk=piece_id)
        if piece.decommissioned:
            raise serializers.ValidationError({"detail": "inactive_piece"})
        photo = get_object_or_404(Photo, pk=photo_id, piece=piece)
        old = {
            "photos": list(piece.photos.values_list("pk", flat=True)),
            "photo": snapshot(photo),
        }
        photo.delete()
        record(
            user=request.user,
            action_type=AuditEntry.Action.MODIFY,
            entity="piece",
            entity_id=piece.pk,
            old=old,
            new={"photos": list(piece.photos.values_list("pk", flat=True))},
        )
    return Response({"deleted": photo_id})


@api_view(["PATCH"])
@requiere_permiso("piezas.actualizar")
def reorder_photos(request, piece_id):
    serializer = PhotoOrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    photo_ids = serializer.validated_data["photos"]
    with transaction.atomic():
        piece = get_object_or_404(Piece.objects.select_for_update(), pk=piece_id)
        if piece.decommissioned:
            raise serializers.ValidationError({"detail": "inactive_piece"})
        photos = list(piece.photos.only("id", "position"))
        old_ids = [photo.pk for photo in photos]
        if len(photo_ids) != len(old_ids) or set(photo_ids) != set(old_ids):
            raise serializers.ValidationError({"photos": "invalid_photo_order"})
        if photo_ids != old_ids:
            by_id = {photo.pk: photo for photo in photos}
            for position, photo_id in enumerate(photo_ids):
                by_id[photo_id].position = position
            Photo.objects.bulk_update(photos, ["position"])
            record(
                user=request.user,
                action_type=AuditEntry.Action.MODIFY,
                entity="piece",
                entity_id=piece.pk,
                old={"photos": old_ids},
                new={"photos": photo_ids},
            )
    return Response({"photos": photo_ids})


@api_view(["POST"])
@requiere_permiso("piezas.dar_baja")
def decommission(request, piece_id):
    from .services import decommission_piece, require_museologist
    from .serializers import DecommissionSerializer
    require_museologist(request.user)
    get_object_or_404(Piece, pk=piece_id)
    serializer = DecommissionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    piece = decommission_piece(user=request.user, piece_id=piece_id, **serializer.validated_data)
    return Response(PieceSerializer(piece).data)


@api_view(["POST"])
@requiere_permiso("piezas.marcar_robo_extravio")
def missing(request, piece_id):
    from .services import mark_missing, require_museologist
    from .serializers import MissingPieceSerializer
    require_museologist(request.user)
    get_object_or_404(Piece, pk=piece_id)
    serializer = MissingPieceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    piece = mark_missing(user=request.user, piece_id=piece_id, **serializer.validated_data)
    return Response(PieceSerializer(piece).data)


@api_view(["POST"])
@requiere_permiso("piezas.registrar_prestamo")
def loan(request, piece_id):
    require_museologist(request.user)
    get_object_or_404(Piece, pk=piece_id)
    serializer = LoanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    piece = loan_piece(user=request.user, piece_id=piece_id, **serializer.validated_data)
    return Response(PieceSerializer(piece).data)


@api_view(["POST"])
@requiere_permiso("piezas.registrar_prestamo")
def return_loan(request, piece_id):
    require_museologist(request.user)
    get_object_or_404(Piece, pk=piece_id)
    piece = return_piece(user=request.user, piece_id=piece_id)
    return Response(PieceSerializer(piece).data)


@api_view(["POST"])
@requiere_permiso("piezas.marcar_robo_extravio")
def recover(request, piece_id):
    from .services import recover_piece
    require_museologist(request.user)
    get_object_or_404(Piece, pk=piece_id)
    piece = recover_piece(user=request.user, piece_id=piece_id)
    return Response(PieceSerializer(piece).data)


@api_view(["POST"])
@requiere_permiso("piezas.dar_baja")
def reactivate(request, piece_id):
    from .services import reactivate_piece
    require_museologist(request.user)
    get_object_or_404(Piece, pk=piece_id)
    piece = reactivate_piece(user=request.user, piece_id=piece_id)
    return Response(PieceSerializer(piece).data)
