from audit.models import AuditEntry
from audit.services import audited_create, record, snapshot
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from . import schema as docs

from .models import Evento
from core.permissions import permisos_para, registrar_denegacion, requiere_permiso
from .serializers import EventoSerializer, EventoUpdateSerializer, EventoAsistenciaSerializer


# SIAM-12 y SIAM-13: registro de eventos y consulta pública.
@never_cache
@extend_schema(tags=["Events"], methods=["GET"], summary="List scheduled public events", auth=[],
               responses={200: docs.PublicEventSerializer(many=True)})
@extend_schema(tags=["Events"], methods=["POST"], summary="Create an event", auth=[{"cookieAuth": []}], request=EventoSerializer,
               description="Permission: eventos.crear. New events must have a future date and expected attendance of at least one.",
               responses={201: EventoSerializer, **docs.ERRORS})
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def events(request):
    # SIAM-13: solo eventos públicos programados.
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

    verificar_permiso_evento(request, "eventos.crear")

    serializer = EventoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    audited_create(
        user=request.user,
        entity="evento",
        create=lambda: serializer.save(creado_por=request.user),
    )

    return Response(serializer.data, status=201)


# SIAM-14 y SIAM-16: eventos internos y sus datos de asistencia.
@never_cache
@extend_schema(tags=["Events"], summary="List scheduled public and private events",
               description="Permission: eventos.ver_privados (all staff roles). Includes expected and actual attendance.",
               responses={200: docs.InternalEventSerializer(many=True), **docs.ERRORS})
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
            "asistentes_esperados": evento.asistentes_esperados,
            "asistentes_reales": evento.asistentes_reales,
        }
        for evento in eventos
    ])


def verificar_permiso_evento(request, permiso):
    if not request.user.is_authenticated:
        raise NotAuthenticated(
            "Debe iniciar sesión para gestionar eventos."
        )

    if permiso not in permisos_para(request.user):
        registrar_denegacion(request, permiso)
        raise PermissionDenied(
            "No tiene permiso para realizar esta operación."
        )


# SIAM-15: consulta individual y modificación de eventos.
@never_cache
@extend_schema(tags=["Events"], methods=["GET"], summary="Get an event",
               description="Permission: eventos.actualizar.", responses={200: EventoSerializer, **docs.ERRORS})
@extend_schema(tags=["Events"], methods=["PATCH"], summary="Update an event", request=EventoUpdateSerializer,
               description="Permission: eventos.actualizar. Only scheduled future events can be edited; a replacement date must also be in the future.",
               responses={200: EventoSerializer, **docs.ERRORS})
@api_view(["GET", "PATCH"])
def event_detail(request, event_id):
    verificar_permiso_evento(
        request,
        "eventos.actualizar",
    )

    if request.method == "GET":
        evento = get_object_or_404(
            Evento,
            pk=event_id,
        )

        return Response(EventoSerializer(evento).data)

    with transaction.atomic():
        evento = get_object_or_404(
            Evento.objects.select_for_update(),
            pk=event_id,
        )

        if evento.estado != Evento.Estado.PROGRAMADO:
            raise serializers.ValidationError(
                "No se puede modificar un evento cancelado."
            )

        if evento.fecha <= timezone.now():
            raise serializers.ValidationError(
                "No se puede modificar un evento que ya ocurrió."
            )

        old = snapshot(evento)

        serializer = EventoUpdateSerializer(
            evento,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        # Revalidación para evitar modificar un evento vencido.
        if evento.fecha <= timezone.now():
            raise serializers.ValidationError(
                "No se puede modificar un evento que ya ocurrió."
            )

        serializer.save()

        record(
            user=request.user,
            action_type=AuditEntry.Action.MODIFY,
            entity="evento",
            entity_id=evento.pk,
            old=old,
            new=snapshot(evento),
        )

        return Response(serializer.data)


# SIAM-15: cancelación confirmada sin eliminar el registro.
@never_cache
@extend_schema(tags=["Events"], summary="Cancel an event", request=docs.CONFIRM,
               description="Permission: eventos.cancelar. Send confirm=true; only future scheduled events can be cancelled.",
               responses={200: docs.EVENT_RESULT, **docs.ERRORS})
@api_view(["POST"])
def cancel_event(request, event_id):
    verificar_permiso_evento(
        request,
        "eventos.cancelar",
    )

    if (
        not isinstance(request.data, dict)
        or request.data.get("confirm") is not True
    ):
        raise serializers.ValidationError({
            "confirm": "Debe confirmar la cancelación con true."
        })

    with transaction.atomic():
        evento = get_object_or_404(
            Evento.objects.select_for_update(),
            pk=event_id,
        )

        if evento.estado == Evento.Estado.CANCELADO:
            raise serializers.ValidationError(
                "El evento ya está cancelado."
            )

        if evento.fecha <= timezone.now():
            raise serializers.ValidationError(
                "No se puede cancelar un evento que ya ocurrió."
            )

        old = snapshot(evento)

        evento.estado = Evento.Estado.CANCELADO
        evento.save(update_fields=["estado", "actualizado_en"])

        record(
            user=request.user,
            action_type=AuditEntry.Action.MODIFY,
            entity="evento",
            entity_id=evento.pk,
            old=old,
            new=snapshot(evento),
        )

        return Response({
            "detail": "Evento cancelado correctamente.",
            "evento": EventoSerializer(evento).data,
        })


# SIAM-16: registro o corrección de asistencia real.
@never_cache
@extend_schema(tags=["Events"], summary="Record or correct attendance", request=EventoAsistenciaSerializer,
               description="Permission: eventos.registrar_asistencia. Event must have occurred and cannot be cancelled. Send a non-negative JSON integer.",
               responses={200: docs.EVENT_RESULT, **docs.ERRORS})
@api_view(["PATCH"])
def event_attendance(request, event_id):
    verificar_permiso_evento(
        request,
        "eventos.registrar_asistencia",
    )

    serializer = EventoAsistenciaSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        evento = get_object_or_404(
            Evento.objects.select_for_update(),
            pk=event_id,
        )

        if evento.estado != Evento.Estado.PROGRAMADO:
            raise serializers.ValidationError(
                "No se puede registrar asistencia en un evento cancelado."
            )

        if evento.fecha > timezone.now():
            raise serializers.ValidationError(
                "Solo se puede registrar asistencia en eventos que ya ocurrieron."
            )

        old = snapshot(evento)

        evento.asistentes_reales = serializer.validated_data["asistentes_reales"]
        evento.save(update_fields=["asistentes_reales", "actualizado_en"])

        record(
            user=request.user,
            action_type=AuditEntry.Action.MODIFY,
            entity="evento",
            entity_id=evento.pk,
            old=old,
            new=snapshot(evento),
        )

        return Response({
            "detail": "Asistencia real registrada correctamente.",
            "evento": EventoSerializer(evento).data,
        })
