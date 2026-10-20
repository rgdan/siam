from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .authentication import SessionAuthentication


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


# Comprueba que la API responde, sin exigir una sesión ni consultar la base de datos.
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"estado": "ok"})


# Entrega un token CSRF y permite que Django envíe su cookie al navegador.
@never_cache
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


# Valida las credenciales, abre la sesión y devuelve un token CSRF actualizado.
@never_cache
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_in(request):
    # SessionAuthentication solo exige CSRF con sesión; el login también lo necesita.
    SessionAuthentication().enforce_csrf(request)
    credentials = LoginSerializer(data=request.data)
    if not credentials.is_valid():
        raise AuthenticationFailed("Correo o contraseña incorrectos")

    email = get_user_model().objects.normalize_email(credentials.validated_data["email"])
    user = authenticate(request=request, email=email, password=credentials.validated_data["password"])
    if user is None:
        raise AuthenticationFailed("Correo o contraseña incorrectos")

    login(request, user)
    return Response({"detail": "Sesión iniciada.", "csrfToken": get_token(request)})


# Devuelve los datos de la cuenta identificada por la sesión, nunca la contraseña.
@never_cache
@api_view(["GET"])
def me(request):
    user = request.user
    return Response({
        "id": user.pk,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    })


# Invalida la sesión en Django para que su cookie deje de permitir el acceso.
@never_cache
@api_view(["POST"])
def sign_out(request):
    logout(request)
    return Response({"detail": "Sesión cerrada."})


# Sustituye la página HTML de rechazo CSRF por una respuesta JSON sin detalles internos.
def csrf_failure(request, reason=""):
    return JsonResponse({"detail": "Verificación CSRF fallida."}, status=403)


# Responde en JSON cuando Django rechaza una solicitud incorrecta.
def bad_request(request, exception):
    return JsonResponse({"detail": "Solicitud incorrecta."}, status=400)


# Responde en JSON cuando Django deniega el acceso, sin devolver datos del recurso.
def permission_denied(request, exception):
    return JsonResponse({"detail": "Acceso denegado."}, status=403)


# Mantiene el formato JSON cuando la URL solicitada no existe.
def not_found(request, exception):
    return JsonResponse({"detail": "Recurso no encontrado."}, status=404)


# Devuelve un error JSON genérico sin exponer la excepción ni su traza.
def server_error(request):
    return JsonResponse({"detail": "Error interno del servidor."}, status=500)
