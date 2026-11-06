from api.permissions import requiere_permiso
from api import schema as docs
from drf_spectacular.utils import OpenApiParameter, extend_schema
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .defaults import DEFAULTS, default_for
from .serializers import ConfigurationSerializer
from .services import current_configuration, update_configuration


@never_cache
@extend_schema(tags=["Configuration"], summary="Get public museum information", auth=[], responses={200: ConfigurationSerializer})
@api_view(["GET"])
@permission_classes([AllowAny])
def public_configuration(request):
    return Response(current_configuration())


@never_cache
@extend_schema(tags=["Configuration"], methods=["GET"], summary="Get museum settings and defaults",
               description="Permission: sistema.configurar.", responses={200: docs.CONFIGURATION, **docs.ERRORS})
@extend_schema(tags=["Configuration"], methods=["PATCH"], summary="Update museum settings", request=ConfigurationSerializer,
               description="Permission: sistema.configurar. Opening hours must include all seven keys: 0=Sunday through 6=Saturday. Set both hours to null for a closed day.",
               responses={200: docs.CONFIGURATION, **docs.ERRORS})
@api_view(["GET", "PATCH"])
@requiere_permiso("sistema.configurar")
def configuration(request):
    if request.method == "PATCH":
        serializer = ConfigurationSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = update_configuration(
            user=request.user, values=serializer.validated_data
        )
    else:
        values = current_configuration()
    return Response(
        {"values": values, "defaults": {key: default_for(key) for key in DEFAULTS}}
    )


@never_cache
@extend_schema(tags=["Configuration"], summary="Restore one setting to its default", request=None,
               description="Permission: sistema.configurar. Returns all current values.",
               parameters=[OpenApiParameter("key", str, OpenApiParameter.PATH, enum=list(DEFAULTS))],
               responses={200: ConfigurationSerializer, **docs.ERRORS})
@api_view(["POST"])
@requiere_permiso("sistema.configurar")
def reset_parameter(request, key):
    if key not in DEFAULTS:
        raise NotFound("Parámetro desconocido.")
    return Response(
        update_configuration(user=request.user, values={key: default_for(key)})
    )
