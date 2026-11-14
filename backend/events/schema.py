from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as s
from core.schema import ERRORS, DATE_FILTERS, CONFIRM
from .serializers import EventoSerializer


class PublicEventSerializer(EventoSerializer):
    class Meta(EventoSerializer.Meta):
        fields = ["id", "fecha", "descripcion", "ubicacion", "tipo"]


class InternalEventSerializer(EventoSerializer):
    class Meta(EventoSerializer.Meta):
        fields = [*PublicEventSerializer.Meta.fields, "asistentes_esperados", "asistentes_reales"]


EVENT_RESULT = inline_serializer("EventResult", {"detail": s.CharField(), "evento": EventoSerializer()})


class AttendanceTotalsSerializer(s.Serializer):
    asistentes_esperados = s.IntegerField()
    asistentes_reales = s.IntegerField()
    cumplimiento_porcentaje = s.FloatField(allow_null=True)


class AttendanceRowSerializer(s.Serializer):
    id = s.IntegerField()
    fecha = s.DateTimeField()
    descripcion = s.CharField()
    tipo = s.CharField()
    asistentes_esperados = s.IntegerField()
    asistentes_reales = s.IntegerField(allow_null=True)
    estado_asistencia = s.CharField()
    cumplimiento_porcentaje = s.FloatField(allow_null=True)


class AttendanceReportSerializer(s.Serializer):
    titulo = s.CharField()
    filtros = s.DictField(child=s.DateField(allow_null=True))
    eventos = AttendanceRowSerializer(many=True)
    totales = AttendanceTotalsSerializer()
    resumen = s.DictField(child=s.IntegerField())
    mensaje = s.CharField(allow_null=True)

