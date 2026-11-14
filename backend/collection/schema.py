from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as s
from core.schema import ERRORS
from .models import Piece
from .serializers import PhotoSerializer, PieceSerializer


PIECE_STATES = Piece._meta.get_field("state").choices


class PieceDetailSerializer(PieceSerializer):
    photos = PhotoSerializer(many=True)
    history = s.ListField(child=s.DictField(), help_text="id, timestamp, user (name or null), action, changes.")

    class Meta(PieceSerializer.Meta):
        fields = [*PieceSerializer.Meta.fields, "photos", "history"]


PHOTO_RESULTS = inline_serializer("PhotoUploadResult", {
    "results": s.ListField(child=s.DictField(), help_text="Each item contains index and id, or index and errors. Partial success is possible."),
})


PHOTO_ORDER = inline_serializer("PhotoOrderResult", {"photos": s.ListField(child=s.IntegerField())})


class CollectionReportSerializer(s.Serializer):
    generated_at = s.DateTimeField()
    filters = s.DictField(child=s.CharField(allow_null=True))
    total = s.IntegerField()
    active = s.IntegerField()
    by_state = s.DictField(child=s.IntegerField())
    missing_breakdown = s.DictField(child=s.IntegerField())
    by_object_type = s.DictField(child=s.IntegerField())
    by_collection = s.DictField(child=s.IntegerField())
    available_filters = s.DictField(child=s.ListField(child=s.CharField()))

