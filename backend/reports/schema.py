from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as s
from core.schema import ERRORS
from core.schema import DATE_FILTERS
from collection.schema import CollectionReportSerializer
from events.schema import AttendanceTotalsSerializer


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

