import logging

from api.permissions import requiere_permiso
from audit.services import audited_create
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import IncidentSerializer

logger = logging.getLogger(__name__)


@never_cache
@api_view(["POST"])
@requiere_permiso("incidencias.registrar")
def register_incident(request):
    serializer = IncidentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        audited_create(
            user=request.user,
            entity="incident",
            create=lambda: serializer.save(user=request.user),
        )
    except Exception:
        logger.exception("No se pudo guardar la incidencia.")
        return Response(
            {
                "code": "incident_save_failed",
                "detail": "No se pudo guardar la incidencia. Inténtelo de nuevo.",
            },
            status=503,
        )
    return Response(serializer.data, status=201)
