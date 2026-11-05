
import calendar
from datetime import date

from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from collection_integrity.reports import collection_report_data
from visitors.models import VisitorEntry

from .models import Evento
from .permissions import requiere_permiso
from .reports import validar_fecha_reporte


def obtener_fechas(request):
    hoy = timezone.localdate()

    inicio_mes = date(hoy.year, hoy.month, 1)
    fin_mes = date(
        hoy.year,
        hoy.month,
        calendar.monthrange(hoy.year, hoy.month)[1],
    )

    inicio_recibido = request.query_params.get("fecha_inicio")
    fin_recibido = request.query_params.get("fecha_fin")

    if not inicio_recibido and not fin_recibido:
        return inicio_mes, fin_mes

    fecha_inicio = validar_fecha_reporte(
        inicio_recibido,
        "fecha_inicio",
    )
    fecha_fin = validar_fecha_reporte(
        fin_recibido,
        "fecha_fin",
    )

    if (
        fecha_inicio is not None
        and fecha_fin is not None
        and fecha_inicio > fecha_fin
    ):
        raise serializers.ValidationError({
            "fecha_fin": "La fecha final no puede ser anterior a la fecha inicial."
        })

    return fecha_inicio, fecha_fin


def datos_visitantes(fecha_inicio, fecha_fin):
    ingresos = VisitorEntry.objects.all()

    if fecha_inicio is not None:
        ingresos = ingresos.filter(timestamp__date__gte=fecha_inicio)

    if fecha_fin is not None:
        ingresos = ingresos.filter(timestamp__date__lte=fecha_fin)

    datos = ingresos.aggregate(
        total=Count("id"),
        nacionales=Count(
            "id", filter=Q(nationality="nacional")
        ),
        extranjeros=Count(
            "id", filter=Q(nationality="extranjero")
        ),
        masculinos=Count(
            "id", filter=Q(sex="masculino")
        ),
        femeninos=Count(
            "id", filter=Q(sex="femenino")
        ),
        mayores=Count(
            "id", filter=Q(age_group="mayor")
        ),
        menores=Count(
            "id", filter=Q(age_group="menor")
        ),
    )

    return {
        "total": datos["total"],
        "por_nacionalidad": {
            "nacional": datos["nacionales"],
            "extranjero": datos["extranjeros"],
        },
        "por_sexo": {
            "masculino": datos["masculinos"],
            "femenino": datos["femeninos"],
        },
        "por_edad": {
            "mayor": datos["mayores"],
            "menor": datos["menores"],
        },
        "mensaje": (
            "Sin datos para el período"
            if datos["total"] == 0
            else None
        ),
    }


def datos_eventos(fecha_inicio, fecha_fin):
    eventos = Evento.objects.all()

    if fecha_inicio is not None:
        eventos = eventos.filter(fecha__date__gte=fecha_inicio)

    if fecha_fin is not None:
        eventos = eventos.filter(fecha__date__lte=fecha_fin)

    resumen = eventos.aggregate(
        total=Count("id"),
        publicos=Count(
            "id",
            filter=Q(tipo=Evento.Tipo.PUBLICO),
        ),
        privados=Count(
            "id",
            filter=Q(tipo=Evento.Tipo.PRIVADO),
        ),
        cancelados=Count(
            "id",
            filter=Q(estado=Evento.Estado.CANCELADO),
        ),
    )

    finalizados = eventos.filter(
        estado=Evento.Estado.PROGRAMADO,
        fecha__lte=timezone.now(),
    )

    asistencia = finalizados.aggregate(
        finalizados=Count("id"),
        con_registro=Count(
            "id",
            filter=Q(asistentes_reales__isnull=False),
        ),
        esperados=Sum(
            "asistentes_esperados",
            filter=Q(asistentes_reales__isnull=False),
        ),
        reales=Sum(
            "asistentes_reales",
            filter=Q(asistentes_reales__isnull=False),
        ),
    )

    total_esperados = asistencia["esperados"] or 0
    total_reales = asistencia["reales"] or 0

    cumplimiento = None

    if asistencia["con_registro"] > 0 and total_esperados > 0:
        cumplimiento = round(
            total_reales / total_esperados * 100,
            2,
        )

    return {
        "total": resumen["total"],
        "publicos": resumen["publicos"],
        "privados": resumen["privados"],
        "cancelados": resumen["cancelados"],
        "asistencia": {
            "eventos_finalizados": asistencia["finalizados"],
            "eventos_con_registro": asistencia["con_registro"],
            "eventos_sin_registro": (
                asistencia["finalizados"]
                - asistencia["con_registro"]
            ),
            "asistentes_esperados": total_esperados,
            "asistentes_reales": total_reales,
            "cumplimiento_porcentaje": cumplimiento,
        },
        "mensaje": (
            "Sin datos para el período"
            if resumen["total"] == 0
            else None
        ),
    }


@never_cache
@api_view(["GET"])
@requiere_permiso("reportes.ver_consolidados")
def consolidated_report(request):
    fecha_inicio, fecha_fin = obtener_fechas(request)

    visitantes = datos_visitantes(fecha_inicio, fecha_fin)
    eventos = datos_eventos(fecha_inicio, fecha_fin)
    colecciones = collection_report_data()

    return Response({
        "titulo": "Reporte consolidado del museo",
        "fecha_generacion": timezone.now().isoformat(),
        "filtros": {
            "fecha_inicio": (
                fecha_inicio.isoformat()
                if fecha_inicio is not None else None
            ),
            "fecha_fin": (
                fecha_fin.isoformat()
                if fecha_fin is not None else None
            ),
        },
        "visitantes": visitantes,
        "eventos": eventos,
        "colecciones": {
            **colecciones,
            "mensaje": (
                "Sin datos para el período"
                if colecciones["total"] == 0
                else None
            ),
        },
    })
