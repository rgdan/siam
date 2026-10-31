import logging

from api.permissions import registrar_denegacion
from audit.services import snapshot
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from .models import Piece
from .serializers import (
    HistorySerializer,
    PhotoSerializer,
    PieceSerializer,
    UploadSerializer,
)
from .services import _finish, attach_photo, register_piece

logger = logging.getLogger(__name__)


class CuratorOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_active and request.user.role == "museologo":
            return True
        if request.user.is_authenticated:
            registrar_denegacion(request, "piezas.actualizar")
        return False


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, CuratorOnly])
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
@permission_classes([IsAuthenticated, CuratorOnly])
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
        data["history"] = HistorySerializer(
            piece.history.select_related("user").order_by("-timestamp", "-id"),
            many=True,
        ).data
        data["photos"] = PhotoSerializer(piece.photos.all(), many=True).data
        return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, CuratorOnly])
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
