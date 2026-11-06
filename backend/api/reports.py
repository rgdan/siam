
from datetime import date
import re

from django.utils import timezone
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from . import schema as docs

from .models import Evento, User
from .permissions import (
    registrar_denegacion,
    requiere_permiso,
)


# SIAM-17: valida las fechas opcionales del reporte.
def validar_fecha_reporte(valor, campo):
    if valor is None or valor == "":
        return None

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        raise serializers.ValidationError({
            campo: "La fecha debe tener el formato AAAA-MM-DD."
        })

    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise serializers.ValidationError({
            campo: "Ingrese una fecha válida."
        }) from None


# SIAM-17: compara la asistencia esperada y la real.
@never_cache
@extend_schema(tags=["Reports"], summary="Compare expected and actual attendance",
               description="Coordinator role only, including an explicit role check. Includes past non-cancelled events. Missing attendance is excluded from totals. Without dates, includes all finished events.",
               parameters=docs.DATE_FILTERS, responses={200: docs.AttendanceReportSerializer, **docs.ERRORS})
@api_view(["GET"])
@requiere_permiso("eventos.generar_reportes")
def attendance_report(request):

    # El reporte está reservado al rol Coordinador.
    if request.user.role != User.Role.COORDINADOR:
        registrar_denegacion(
            request,
            "eventos.generar_reportes",
        )
        raise PermissionDenied(
            "Solo el coordinador puede generar este reporte."
        )

    fecha_inicio = validar_fecha_reporte(
        request.query_params.get("fecha_inicio"),
        "fecha_inicio",
    )

    fecha_fin = validar_fecha_reporte(
        request.query_params.get("fecha_fin"),
        "fecha_fin",
    )

    if (
        fecha_inicio is not None
        and fecha_fin is not None
        and fecha_inicio > fecha_fin
    ):
        raise serializers.ValidationError({
            "fecha_fin": (
                "La fecha final no puede ser anterior "
                "a la fecha inicial."
            )
        })

    # Solo se incluyen eventos realizados y no cancelados.
    eventos = Evento.objects.filter(
        estado=Evento.Estado.PROGRAMADO,
        fecha__lte=timezone.now(),
    )

    # Ambos filtros son opcionales.
    if fecha_inicio is not None:
        eventos = eventos.filter(
            fecha__date__gte=fecha_inicio,
        )

    if fecha_fin is not None:
        eventos = eventos.filter(
            fecha__date__lte=fecha_fin,
        )

    eventos = eventos.order_by("fecha", "id")

    filas = []

    total_esperados = 0
    total_reales = 0
    cantidad_con_registro = 0
    cantidad_sin_registro = 0

    for evento in eventos:
        registrado = evento.asistentes_reales is not None

        if registrado:
            # Solo estos eventos participan en los totales.
            total_esperados += evento.asistentes_esperados
            total_reales += evento.asistentes_reales
            cantidad_con_registro += 1

            cumplimiento = round(
                (
                    evento.asistentes_reales
                    / evento.asistentes_esperados
                ) * 100,
                2,
            )

            asistencia_real = evento.asistentes_reales
        else:
            cantidad_sin_registro += 1
            cumplimiento = None
            asistencia_real = None

        filas.append({
            "id": evento.id,
            "fecha": evento.fecha,
            "descripcion": evento.descripcion,
            "tipo": evento.tipo,
            "asistentes_esperados": evento.asistentes_esperados,
            "asistentes_reales": asistencia_real,
            "estado_asistencia": (
                "Registrada"
                if registrado
                else "Sin registro"
            ),
            "cumplimiento_porcentaje": cumplimiento,
        })

    # El cumplimiento general también excluye eventos
    # que todavía no tienen asistencia real registrada.
    cumplimiento_general = None

    if cantidad_con_registro > 0 and total_esperados > 0:
        cumplimiento_general = round(
            (total_reales / total_esperados) * 100,
            2,
        )

    return Response({
        "titulo": "Reporte comparativo de asistencia",
        "filtros": {
            "fecha_inicio": (
                fecha_inicio.isoformat()
                if fecha_inicio is not None
                else None
            ),
            "fecha_fin": (
                fecha_fin.isoformat()
                if fecha_fin is not None
                else None
            ),
        },
        "eventos": filas,
        "totales": {
            "asistentes_esperados": total_esperados,
            "asistentes_reales": total_reales,
            "cumplimiento_porcentaje": cumplimiento_general,
        },
        "resumen": {
            "eventos_mostrados": len(filas),
            "eventos_con_registro": cantidad_con_registro,
            "eventos_sin_registro": cantidad_sin_registro,
        },
        "mensaje": (
            "No hay eventos para el rango seleccionado"
            if not filas
            else None
        ),
    })
