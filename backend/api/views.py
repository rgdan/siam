
from audit.models import AuditEntry
from audit.services import audited_create, record, snapshot
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, NotAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .authentication import SessionAuthentication
from .models import Evento
from .permissions import permisos_para, registrar_denegacion, requiere_permiso
from .serializers import UserSerializer, UserUpdateSerializer, EventoSerializer


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"estado": "ok"})


@never_cache
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@never_cache
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_in(request):

    SessionAuthentication().enforce_csrf(request)
    credentials = LoginSerializer(data=request.data)
    if not credentials.is_valid():
        record(user=None, action_type=AuditEntry.Action.FAILED_LOGIN, entity="user")
        raise AuthenticationFailed("Correo o contraseña incorrectos")

    email = get_user_model().objects.normalize_email(credentials.validated_data["email"])
    user = authenticate(request=request, email=email, password=credentials.validated_data["password"])
    if user is None:
        attempted = get_user_model().objects.filter(email__iexact=email).first()
        record(
            user=attempted,
            action_type=AuditEntry.Action.FAILED_LOGIN,
            entity="user",
            entity_id=attempted.pk if attempted else "",
        )
        raise AuthenticationFailed("Correo o contraseña incorrectos")

    with transaction.atomic():
        login(request, user)
        record(user=user, action_type=AuditEntry.Action.LOGIN, entity="user", entity_id=user.pk)
    return Response({"detail": "Sesión iniciada.", "csrfToken": get_token(request)})


@never_cache
@api_view(["GET"])
def me(request):
    user = request.user
    return Response({
        "id": user.pk,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "permissions": sorted(permisos_para(user)),
    })


@never_cache
@api_view(["POST"])
def sign_out(request):
    logout(request)
    return Response({"detail": "Sesión cerrada."})


@never_cache
@api_view(["GET", "POST"])
@requiere_permiso({"GET": "usuarios.consultar", "POST": "usuarios.crear"})
def users(request):
    if request.method == "GET":
        accounts = get_user_model().objects.order_by("id")
        return Response(UserSerializer(accounts, many=True).data)

    account = UserSerializer(data=request.data)
    account.is_valid(raise_exception=True)
    try:
        audited_create(user=request.user, entity="user", create=account.save)
    except DjangoValidationError as error:
        raise serializers.ValidationError(error.message_dict) from None
    except IntegrityError:
        raise serializers.ValidationError({
            "email": ["Ya existe una cuenta con este correo."]
        }) from None

    return Response(account.data, status=201)


@never_cache
@api_view(["PATCH", "DELETE"])
@requiere_permiso({
    "PATCH": "usuarios.actualizar",
    "DELETE": "usuarios.eliminar",
})
def user_detail(request, user_id):
    try:
        with transaction.atomic():

            actor = get_user_model().objects.filter(pk=request.user.pk).first()
            allowed = permisos_para(actor)
            required = (
                "usuarios.eliminar"
                if request.method == "DELETE"
                else "usuarios.actualizar"
            )

            if required not in allowed:
                raise PermissionDenied("Acceso denegado.")

            if (
                request.method == "PATCH"
                and isinstance(request.data, dict)
                and "role" in request.data
                and "usuarios.asignar_rol" not in allowed
            ):
                required = "usuarios.asignar_rol"
                raise PermissionDenied("Acceso denegado.")

            account = get_object_or_404(get_user_model(), pk=user_id)
            old = snapshot(account)

            if request.method == "DELETE":
                if (
                    not isinstance(request.data, dict)
                    or request.data.get("confirm") is not True
                ):
                    raise serializers.ValidationError({
                        "confirm": "Confirme la eliminación con true."
                    })

                if account.pk == request.user.pk:
                    raise serializers.ValidationError(
                        "No puede eliminar su propia cuenta."
                    )

                deactivation = UserUpdateSerializer(
                    account,
                    data={"is_active": False},
                    partial=True,
                    context={"request": request},
                )
                deactivation.is_valid(raise_exception=True)

                if account.has_related_records():
                    deactivation.save()
                    record(
                        user=actor,
                        action_type=AuditEntry.Action.DECOMMISSION,
                        entity="user",
                        entity_id=account.pk,
                        old=old,
                        new=snapshot(account),
                    )
                    return Response({
                        "detail": "La cuenta tiene registros relacionados y fue desactivada.",
                        "action": "deactivated",
                    })

                account_id = account.pk
                account.delete()
                record(
                    user=actor,
                    action_type=AuditEntry.Action.DECOMMISSION,
                    entity="user",
                    entity_id=account_id,
                    old=old,
                )
                return Response({
                    "detail": "Cuenta eliminada.",
                    "action": "deleted",
                })

            changes = UserUpdateSerializer(
                account,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            changes.is_valid(raise_exception=True)

            credential_reset = "password" in changes.validated_data
            changes.save()

            new = snapshot(account)
            if credential_reset:
                new["credential_reset"] = True

            record(
                user=actor,
                action_type=AuditEntry.Action.MODIFY,
                entity="user",
                entity_id=account.pk,
                old=old,
                new=new,
            )
            return Response(changes.data)

    except PermissionDenied:
        # Fuera de la transacción fallida para que el rechazo no borre su propia auditoría.
        registrar_denegacion(request, required)
        raise

    except IntegrityError:
        if request.method == "DELETE":
            raise serializers.ValidationError(
                "No se pudo eliminar la cuenta por sus registros relacionados."
            ) from None

        raise serializers.ValidationError({
            "email": ["Ya existe una cuenta con este correo."]
        }) from None


# SIAM-12 y SIAM-13: registro de eventos y consulta pública.
@never_cache
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def events(request):
    # SIAM-13: cualquier visitante puede consultar eventos públicos programados.
    if request.method == "GET":
        eventos = Evento.objects.filter(
            tipo=Evento.Tipo.PUBLICO,
            estado=Evento.Estado.PROGRAMADO,
        ).order_by("fecha", "id")

        return Response([
            {
                "id": evento.pk,
                "fecha": evento.fecha,
                "descripcion": evento.descripcion,
                "ubicacion": evento.ubicacion,
                "tipo": evento.tipo,
            }
            for evento in eventos
        ])

    # SIAM-12: registrar eventos requiere una cuenta activa de coordinador.
    if not request.user.is_authenticated:
        raise NotAuthenticated("Debe iniciar sesión para registrar eventos.")

    if (
        not request.user.is_active
        or request.user.role != "coordinador"
        or "eventos.crear" not in permisos_para(request.user)
    ):
        registrar_denegacion(request, "eventos.crear")
        raise PermissionDenied("Solo el coordinador puede registrar eventos.")

    serializer = EventoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    audited_create(
        user=request.user,
        entity="evento",
        create=lambda: serializer.save(creado_por=request.user),
    )

    return Response(serializer.data, status=201)


# SIAM-14: consulta de eventos para el personal interno autorizado.
@never_cache
@api_view(["GET"])
@requiere_permiso("eventos.ver_privados")
def internal_events(request):
    eventos = Evento.objects.filter(
        estado=Evento.Estado.PROGRAMADO,
        tipo__in=[Evento.Tipo.PUBLICO, Evento.Tipo.PRIVADO],
    ).order_by("fecha", "id")

    return Response([
        {
            "id": evento.pk,
            "fecha": evento.fecha,
            "descripcion": evento.descripcion,
            "ubicacion": evento.ubicacion,
            "tipo": evento.tipo,
        }
        for evento in eventos
    ])


def csrf_failure(request, reason=""):
    return JsonResponse({"detail": "Verificación CSRF fallida."}, status=403)


def bad_request(request, exception):
    return JsonResponse({"detail": "Solicitud incorrecta."}, status=400)


def permission_denied(request, exception):
    return JsonResponse({"detail": "Acceso denegado."}, status=403)


def not_found(request, exception):
    return JsonResponse({"detail": "Recurso no encontrado."}, status=404)


def server_error(request):
    return JsonResponse({"detail": "Error interno del servidor."}, status=500)
