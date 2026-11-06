import logging
from drf_spectacular.utils import OpenApiResponse, extend_schema
from api import schema as docs

from api.permissions import requiere_permiso
from audit.services import audited_create
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import VisitorEntrySerializer

logger = logging.getLogger(__name__)


@never_cache
@extend_schema(tags=["Visitors"], summary="Record an anonymous visitor entry", request=VisitorEntrySerializer,
               description="Permission: visitantes.registrar. Records demographic categories only; no visitor name or identity number. Staff account and timestamp are server-owned.",
               responses={201: VisitorEntrySerializer, 503: OpenApiResponse(description="Entry could not be saved; nothing was committed."), **docs.ERRORS})
@api_view(["POST"])
@requiere_permiso("visitantes.registrar")
def register_entry(request):
    serializer = VisitorEntrySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        audited_create(
            user=request.user,
            entity="visitor_entry",
            create=lambda: serializer.save(user=request.user),
        )
    except Exception:
        logger.exception("No se pudo guardar el ingreso de visitante.")
        return Response(
            {
                "code": "visitor_entry_save_failed",
                "detail": "No se pudo guardar el ingreso. Inténtelo de nuevo.",
            },
            status=503,
        )
    return Response(serializer.data, status=201)
