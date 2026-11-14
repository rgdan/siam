from audit.models import AuditEntry
from audit.services import audited_create, record, snapshot
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from . import schema as docs

from .authentication import SessionAuthentication
from core.permissions import permisos_para, registrar_denegacion, requiere_permiso
from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


@never_cache
@extend_schema(tags=["Authentication"], summary="Get a CSRF token and cookie", auth=[], responses={200: docs.CSRF})
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@never_cache
@extend_schema(tags=["Authentication"], summary="Sign in", auth=[], request=LoginSerializer,
               description="Requires the CSRF cookie and matching X-CSRFToken header, even before login. Rotates CSRF and creates sessionid.",
               responses={200: docs.LOGIN_RESULT, **docs.ERRORS})
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
        record(
            user=user,
            action_type=AuditEntry.Action.LOGIN,
            entity="user",
            entity_id=user.pk,
        )

    return Response({
        "detail": "Sesión iniciada.",
        "csrfToken": get_token(request),
    })


@never_cache
@extend_schema(tags=["Authentication"], summary="Get the current account and permissions",
               responses={200: docs.SessionUserSerializer, **docs.ERRORS})
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
@extend_schema(tags=["Authentication"], summary="Sign out", request=None, responses={200: docs.DETAIL, **docs.ERRORS})
@api_view(["POST"])
def sign_out(request):
    logout(request)
    return Response({"detail": "Sesión cerrada."})


@never_cache
@extend_schema(tags=["Users"], methods=["GET"], summary="List staff accounts",
               description="Permission: usuarios.consultar (system administrator).", responses={200: UserSerializer(many=True), **docs.ERRORS})
@extend_schema(tags=["Users"], methods=["POST"], summary="Create a staff account", request=UserSerializer,
               description="Permission: usuarios.crear. Passwords require at least 8 characters, including letters and digits.",
               responses={201: UserSerializer, **docs.ERRORS})
@api_view(["GET", "POST"])
@requiere_permiso({
    "GET": "usuarios.consultar",
    "POST": "usuarios.crear",
})
def users(request):
    if request.method == "GET":
        accounts = get_user_model().objects.order_by("id")
        return Response(UserSerializer(accounts, many=True).data)

    account = UserSerializer(data=request.data)
    account.is_valid(raise_exception=True)

    try:
        audited_create(
            user=request.user,
            entity="user",
            create=account.save,
        )
    except DjangoValidationError as error:
        raise serializers.ValidationError(error.message_dict) from None
    except IntegrityError:
        raise serializers.ValidationError({
            "email": ["Ya existe una cuenta con este correo."]
        }) from None

    return Response(account.data, status=201)


@never_cache
@extend_schema(tags=["Users"], methods=["PATCH"], summary="Update a staff account", request=UserUpdateSerializer,
               description="Permission: usuarios.actualizar; changing role also requires usuarios.asignar_rol. Cannot deactivate yourself or remove the last active system administrator.",
               responses={200: UserSerializer, **docs.ERRORS})
@extend_schema(tags=["Users"], methods=["DELETE"], summary="Delete or deactivate a staff account", request=docs.CONFIRM,
               description="Permission: usuarios.eliminar. Send confirm=true. Accounts with related records are deactivated instead of deleted.",
               responses={200: docs.DELETE_USER, **docs.ERRORS})
@api_view(["PATCH", "DELETE"])
@requiere_permiso({
    "PATCH": "usuarios.actualizar",
    "DELETE": "usuarios.eliminar",
})
def user_detail(request, user_id):
    try:
        with transaction.atomic():

            actor = get_user_model().objects.filter(
                pk=request.user.pk
            ).first()

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

            account = get_object_or_404(
                get_user_model(),
                pk=user_id,
            )

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
        # La auditoría del rechazo se registra fuera de la transacción.
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
