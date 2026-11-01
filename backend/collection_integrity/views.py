import logging

from api.permissions import requiere_permiso
from audit.services import snapshot
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Piece
from .serializers import (
    PhotoSerializer,
    PieceSerializer,
    UploadSerializer,
)
from .services import _finish, attach_photo, register_piece

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
@requiere_permiso("piezas.crear")
def pieces(request):
    if request.method == "GET":
        queryset = Piece.objects.order_by("-id")
        state = request.query_params.get("state")
        if state:
            if state not in ["stored", "displayed"]:
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
