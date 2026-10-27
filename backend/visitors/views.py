import logging

from api.permissions import requiere_permiso
from audit.services import audited_create
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import VisitorEntrySerializer

logger = logging.getLogger(__name__)


@never_cache
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
