from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"estado": "ok"})


def bad_request(request, exception):
    return JsonResponse({"detail": "Solicitud incorrecta."}, status=400)


def permission_denied(request, exception):
    return JsonResponse({"detail": "Acceso denegado."}, status=403)


def not_found(request, exception):
    return JsonResponse({"detail": "Recurso no encontrado."}, status=404)


def server_error(request):
    return JsonResponse({"detail": "Error interno del servidor."}, status=500)
