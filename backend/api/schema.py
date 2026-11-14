from core.schema import ERRORS, DATE_FILTERS, CONFIRM, DETAIL, HEALTH
"""Response shapes that are assembled by views rather than model serializers."""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as s

from collection.serializers import PhotoSerializer, PieceSerializer
from collection.models import Piece
from incidents.serializers import IncidentSerializer
from system_configuration.serializers import ConfigurationSerializer
from events.schema import AttendanceTotalsSerializer

PIECE_STATES = Piece._meta.get_field("state").choices






INCIDENT_PAGE = inline_serializer("IncidentPage", {
    "count": s.IntegerField(), "next": s.URLField(allow_null=True),
    "previous": s.URLField(allow_null=True), "results": IncidentSerializer(many=True),
})
CONFIGURATION = inline_serializer("ConfigurationResult", {
    "values": ConfigurationSerializer(), "defaults": ConfigurationSerializer(),
})


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


class VisitorTotalsSerializer(s.Serializer):
    total = s.IntegerField()
    por_nacionalidad = s.DictField(child=s.IntegerField())
    por_sexo = s.DictField(child=s.IntegerField())
    por_edad = s.DictField(child=s.IntegerField())
    mensaje = s.CharField(allow_null=True)




class EventAttendanceTotalsSerializer(AttendanceTotalsSerializer):
    eventos_finalizados = s.IntegerField()
    eventos_con_registro = s.IntegerField()
    eventos_sin_registro = s.IntegerField()


class EventTotalsSerializer(s.Serializer):
    total = s.IntegerField()
    publicos = s.IntegerField()
    privados = s.IntegerField()
    cancelados = s.IntegerField()
    asistencia = EventAttendanceTotalsSerializer()
    mensaje = s.CharField(allow_null=True)


class ConsolidatedCollectionSerializer(CollectionReportSerializer):
    mensaje = s.CharField(allow_null=True)


INCIDENT_TOTALS = inline_serializer("IncidentTotals", {
    "total": s.IntegerField(), "por_categoria": s.DictField(child=s.IntegerField()),
})


class ConsolidatedReportSerializer(s.Serializer):
    titulo = s.CharField()
    fecha_generacion = s.DateTimeField()
    filtros = s.DictField(child=s.DateField(allow_null=True))
    visitantes = VisitorTotalsSerializer()
    eventos = EventTotalsSerializer()
    incidencias = INCIDENT_TOTALS
    colecciones = ConsolidatedCollectionSerializer()




