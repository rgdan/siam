import logging

from api.permissions import requiere_permiso
from audit.services import audited_create
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .serializers import IncidentListFilters, IncidentSerializer
from .models import Incident

logger = logging.getLogger(__name__)


class IncidentPagination(PageNumberPagination):
    page_size = 20


@never_cache
@api_view(["GET", "POST"])
@requiere_permiso("incidencias.registrar")
def register_incident(request):
    if request.method == "GET":
        filters = IncidentListFilters(data=request.query_params)
        filters.is_valid(raise_exception=True)
        ordering = filters.validated_data["ordering"]
        incidents = Incident.objects.select_related("user").order_by(
            ordering, "-pk" if ordering == "-timestamp" else "pk",
        )
        pagination = IncidentPagination()
        page = pagination.paginate_queryset(incidents, request)
        return pagination.get_paginated_response(IncidentSerializer(page, many=True).data)

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
