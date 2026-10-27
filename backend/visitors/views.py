import logging

from api.models import User
from api.permissions import registrar_denegacion
from audit.services import audited_create
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from .serializers import VisitorEntrySerializer

logger = logging.getLogger(__name__)


class GuardaOnly(BasePermission):
    message = "Acceso denegado."

    def has_permission(self, request, view):
        # RF-GRD-01 exige Guarda incluso cuando un administrador hereda el permiso.
        if request.user.is_active and request.user.role == User.Role.GUARDA:
            return True
        registrar_denegacion(request, "visitantes.registrar")
        return False


@never_cache
@api_view(["POST"])
@permission_classes([IsAuthenticated, GuardaOnly])
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
