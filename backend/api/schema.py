"""Response shapes that are assembled by views rather than model serializers."""

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as s

from collection_integrity.serializers import PhotoSerializer, PieceSerializer
from collection_integrity.models import Piece
from incidents.serializers import IncidentSerializer
from system_configuration.serializers import ConfigurationSerializer
from .serializers import EventoSerializer, UserSerializer

PIECE_STATES = Piece._meta.get_field("state").choices


ERRORS = {
    400: OpenApiResponse(OpenApiTypes.OBJECT, description="Invalid input: field errors or detail/non_field_errors."),
    401: OpenApiResponse(description="No active session, or invalid login credentials."),
    403: OpenApiResponse(description="Missing role permission or invalid/missing CSRF token."),
    404: OpenApiResponse(description="Resource or page not found."),
}
DATE_FILTERS = [
    OpenApiParameter("fecha_inicio", OpenApiTypes.DATE, description="Inclusive start date (YYYY-MM-DD), Costa Rica time."),
    OpenApiParameter("fecha_fin", OpenApiTypes.DATE, description="Inclusive end date (YYYY-MM-DD), Costa Rica time."),
]
CONFIRM = inline_serializer("Confirmation", {"confirm": s.BooleanField(help_text="Must be true.")})
DETAIL = inline_serializer("Detail", {"detail": s.CharField()})
HEALTH = inline_serializer("Health", {"estado": s.CharField(default="ok")})
CSRF = inline_serializer("CSRFToken", {"csrfToken": s.CharField()})
LOGIN_RESULT = inline_serializer("LoginResult", {"detail": s.CharField(), "csrfToken": s.CharField()})


class SessionUserSerializer(UserSerializer):
    permissions = s.ListField(child=s.CharField())

    class Meta(UserSerializer.Meta):
        fields = ["id", "full_name", "email", "role", "permissions"]


class PublicEventSerializer(EventoSerializer):
    class Meta(EventoSerializer.Meta):
        fields = ["id", "fecha", "descripcion", "ubicacion", "tipo"]


class InternalEventSerializer(EventoSerializer):
    class Meta(EventoSerializer.Meta):
        fields = [*PublicEventSerializer.Meta.fields, "asistentes_esperados", "asistentes_reales"]


EVENT_RESULT = inline_serializer("EventResult", {"detail": s.CharField(), "evento": EventoSerializer()})
DELETE_USER = inline_serializer("DeleteUserResult", {
    "detail": s.CharField(), "action": s.ChoiceField(choices=["deleted", "deactivated"]),
})
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


class AttendanceTotalsSerializer(s.Serializer):
    asistentes_esperados = s.IntegerField()
    asistentes_reales = s.IntegerField()
    cumplimiento_porcentaje = s.FloatField(allow_null=True)


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
