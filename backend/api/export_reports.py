
from datetime import date
from html import escape
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import api_view

from collection_integrity.reports import collection_report_data
from incidents.models import Incident
from incidents.reports import incident_report_data
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .consolidated_reports import (
    datos_eventos,
    datos_visitantes,
    obtener_fechas,
)
from .models import Evento
from .permissions import requiere_permiso
from .reports import validar_fecha_reporte


def agregar_resumen(secciones, titulo, datos):
    secciones.append({
        "titulo": titulo,
        "columnas": ["Indicador", "Cantidad"],
        "filas": [[nombre, valor] for nombre, valor in datos],
    })


def datos_para_exportar(request, tipo):
    parametros = request.query_params
    filtros = {}

    if tipo == "consolidated":
        inicio, fin = obtener_fechas(request)
        visitantes = datos_visitantes(inicio, fin)
        eventos = datos_eventos(inicio, fin)
        colecciones = collection_report_data()
        incidencias = incident_report_data(inicio, fin)

        filtros = {
            "Fecha inicial": inicio.isoformat() if inicio else "Todas",
            "Fecha final": fin.isoformat() if fin else "Todas",
        }

        secciones = []

        agregar_resumen(secciones, "Visitantes", [
            ("Total de ingresos", visitantes["total"]),
            ("Nacionales", visitantes["por_nacionalidad"]["nacional"]),
            ("Extranjeros", visitantes["por_nacionalidad"]["extranjero"]),
            ("Masculino", visitantes["por_sexo"]["masculino"]),
            ("Femenino", visitantes["por_sexo"]["femenino"]),
            ("Mayores", visitantes["por_edad"]["mayor"]),
            ("Menores", visitantes["por_edad"]["menor"]),
        ])

        asistencia = eventos["asistencia"]

        agregar_resumen(secciones, "Eventos", [
            ("Total de eventos", eventos["total"]),
            ("Públicos", eventos["publicos"]),
            ("Privados", eventos["privados"]),
            ("Cancelados", eventos["cancelados"]),
            ("Finalizados", asistencia["eventos_finalizados"]),
            ("Con asistencia registrada", asistencia["eventos_con_registro"]),
            ("Sin asistencia registrada", asistencia["eventos_sin_registro"]),
            ("Asistentes esperados", asistencia["asistentes_esperados"]),
            ("Asistentes reales", asistencia["asistentes_reales"]),
            (
                "Cumplimiento (%)",
                asistencia["cumplimiento_porcentaje"]
                if asistencia["cumplimiento_porcentaje"] is not None
                else "Sin registro",
            ),
        ])

        agregar_resumen(secciones, "Colecciones", [
            ("Total de piezas", colecciones["total"]),
            ("Piezas activas", colecciones["active"]),
            ("En exhibición", colecciones["by_state"]["displayed"]),
            ("Almacenadas", colecciones["by_state"]["stored"]),
            ("En préstamo", colecciones["by_state"]["loaned"]),
            ("Robadas o extraviadas", colecciones["by_state"]["missing"]),
            ("Dadas de baja", colecciones["by_state"]["decommissioned"]),
        ])

        agregar_resumen(
            secciones,
            "Colecciones por tipo de objeto",
            list(colecciones["by_object_type"].items()),
        )

        agregar_resumen(
            secciones,
            "Colecciones por colección",
            list(colecciones["by_collection"].items()),
        )

        agregar_resumen(secciones, "Incidencias", [
            ("Total de incidencias", incidencias["total"]),
            *[(label, incidencias["por_categoria"][category])
              for category, label in Incident.Category.choices],
        ])

        hay_datos = (
            visitantes["total"] > 0
            or eventos["total"] > 0
            or colecciones["total"] > 0
            or incidencias["total"] > 0
        )

        return {
            "titulo": "Reporte consolidado del museo",
            "filtros": filtros,
            "secciones": secciones,
            "hay_datos": hay_datos,
        }

    if tipo == "collection":
        filtros = {
            clave: parametros[clave]
            for clave in ("state", "object_type", "collection")
            if clave in parametros
        }

        datos = collection_report_data(**filtros)
        secciones = []

        agregar_resumen(secciones, "Resumen de colecciones", [
            ("Total de piezas", datos["total"]),
            ("Piezas activas", datos["active"]),
            ("En exhibición", datos["by_state"]["displayed"]),
            ("Almacenadas", datos["by_state"]["stored"]),
            ("En préstamo", datos["by_state"]["loaned"]),
            ("Robadas o extraviadas", datos["by_state"]["missing"]),
            ("Dadas de baja", datos["by_state"]["decommissioned"]),
            ("Robadas", datos["missing_breakdown"]["stolen"]),
            ("Extraviadas", datos["missing_breakdown"]["lost"]),
        ])

        agregar_resumen(
            secciones,
            "Por tipo de objeto",
            list(datos["by_object_type"].items()),
        )

        agregar_resumen(
            secciones,
            "Por colección",
            list(datos["by_collection"].items()),
        )

        return {
            "titulo": "Reporte de colecciones",
            "filtros": filtros or {"Filtros": "Todos"},
            "secciones": secciones,
            "hay_datos": datos["total"] > 0,
        }

    if tipo == "attendance":
        inicio = validar_fecha_reporte(
            parametros.get("fecha_inicio"), "fecha_inicio"
        )
        fin = validar_fecha_reporte(
            parametros.get("fecha_fin"), "fecha_fin"
        )

        if inicio and fin and inicio > fin:
            raise serializers.ValidationError({
                "fecha_fin": "La fecha final no puede ser anterior a la inicial."
            })

        eventos = Evento.objects.filter(
            estado=Evento.Estado.PROGRAMADO,
            fecha__lte=timezone.now(),
        )

        if inicio:
            eventos = eventos.filter(fecha__date__gte=inicio)
        if fin:
            eventos = eventos.filter(fecha__date__lte=fin)

        eventos = eventos.order_by("fecha", "id")

        filas = []
        esperados = 0
        reales = 0
        con_registro = 0
        sin_registro = 0

        for evento in eventos:
            registrado = evento.asistentes_reales is not None

            if registrado:
                con_registro += 1
                esperados += evento.asistentes_esperados
                reales += evento.asistentes_reales
                cumplimiento = round(
                    evento.asistentes_reales
                    / evento.asistentes_esperados * 100,
                    2,
                )
            else:
                sin_registro += 1
                cumplimiento = "Sin registro"

            filas.append([
                timezone.localtime(evento.fecha).strftime("%d/%m/%Y"),
                evento.descripcion,
                "Público" if evento.tipo == "publico" else "Privado",
                evento.asistentes_esperados,
                evento.asistentes_reales if registrado else "Sin registro",
                cumplimiento,
            ])

        porcentaje_general = (
            round(reales / esperados * 100, 2)
            if con_registro and esperados
            else "Sin registro"
        )

        secciones = [{
            "titulo": "Detalle de asistencia",
            "columnas": [
                "Fecha",
                "Evento",
                "Tipo",
                "Esperados",
                "Reales",
                "Cumplimiento (%)",
            ],
            "filas": filas,
        }]

        agregar_resumen(secciones, "Totales de asistencia", [
            ("Eventos mostrados", len(filas)),
            ("Con asistencia registrada", con_registro),
            ("Sin asistencia registrada", sin_registro),
            ("Asistentes esperados con registro", esperados),
            ("Asistentes reales", reales),
            ("Cumplimiento general (%)", porcentaje_general),
        ])

        return {
            "titulo": "Reporte comparativo de asistencia",
            "filtros": {
                "Fecha inicial": inicio.isoformat() if inicio else "Todas",
                "Fecha final": fin.isoformat() if fin else "Todas",
            },
            "secciones": secciones,
            "hay_datos": bool(filas),
        }

    raise serializers.ValidationError({
        "tipo": "Tipo de reporte no válido."
    })


def generar_excel(datos, usuario):
    libro = Workbook()
    libro.remove(libro.active)

    for indice, seccion in enumerate(datos["secciones"]):
        hoja = libro.create_sheet(
            title=f"{indice + 1} - {seccion['titulo']}"[:31]
        )

        hoja.append([datos["titulo"]])
        hoja.append(["Fecha de generación", timezone.localtime().strftime(
            "%d/%m/%Y %H:%M"
        )])
        hoja.append(["Usuario", usuario.full_name])

        for clave, valor in datos["filtros"].items():
            hoja.append([clave, valor])

        hoja.append([])
        hoja.append([seccion["titulo"]])

        fila_encabezado = hoja.max_row + 1
        hoja.append(seccion["columnas"])

        for fila in seccion["filas"]:
            # Evita que cadenas provenientes de usuarios se interpreten
            # como fórmulas dentro de Excel.
            valores = []
            for valor in fila:
                if isinstance(valor, str) and valor.startswith(
                    ("=", "+", "-", "@")
                ):
                    valor = "'" + valor
                valores.append(valor)
            hoja.append(valores)

        hoja.freeze_panes = f"A{fila_encabezado + 1}"

        for celda in hoja[fila_encabezado]:
            celda.fill = PatternFill(
                "solid", fgColor="12344D"
            )
            celda.font = Font(color="FFFFFF", bold=True)

        hoja["A1"].font = Font(bold=True, size=15)
        hoja[f"A{fila_encabezado - 1}"].font = Font(
            bold=True, size=12
        )

        for columna in hoja.columns:
            letra = get_column_letter(columna[0].column)
            longitud = max(
                (len(str(celda.value or "")) for celda in columna),
                default=12,
            )
            hoja.column_dimensions[letra].width = min(
                max(longitud + 3, 15), 55
            )

        for fila in hoja.iter_rows():
            for celda in fila:
                celda.alignment = Alignment(
                    vertical="top", wrap_text=True
                )

    archivo = BytesIO()
    libro.save(archivo)
    return archivo.getvalue()


def generar_pdf(datos, usuario):
    archivo = BytesIO()
    documento = SimpleDocTemplate(
        archivo,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    estilos = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(
        escape(datos["titulo"]), estilos["Title"]
    ))
    elementos.append(Spacer(1, 12))

    informacion = [
        ("Fecha de generación", timezone.localtime().strftime(
            "%d/%m/%Y %H:%M"
        )),
        ("Usuario", usuario.full_name),
        *datos["filtros"].items(),
    ]

    for clave, valor in informacion:
        elementos.append(Paragraph(
            f"<b>{escape(str(clave))}:</b> {escape(str(valor))}",
            estilos["Normal"],
        ))

    elementos.append(Spacer(1, 16))

    for seccion in datos["secciones"]:
        elementos.append(Paragraph(
            escape(seccion["titulo"]), estilos["Heading2"]
        ))
        elementos.append(Spacer(1, 7))

        if not seccion["filas"]:
            elementos.append(Paragraph(
                "Sin datos para el período", estilos["Normal"]
            ))
            elementos.append(Spacer(1, 14))
            continue

        columnas = len(seccion["columnas"])
        ancho_total = landscape(A4)[0] - 60

        if columnas == 6:
            anchos = [90, 245, 75, 100, 95, 100]
        else:
            anchos = [ancho_total * 0.46, ancho_total * 0.54]

        tabla_datos = [
            [
                Paragraph(
                    f"<b>{escape(str(valor))}</b>",
                    estilos["Normal"],
                )
                for valor in seccion["columnas"]
            ]
        ]

        for fila in seccion["filas"]:
            tabla_datos.append([
                Paragraph(escape(str(valor)), estilos["Normal"])
                for valor in fila
            ])

        tabla = Table(
            tabla_datos,
            colWidths=anchos,
            repeatRows=1,
            hAlign="LEFT",
        )

        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF2")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        elementos.append(tabla)
        elementos.append(Spacer(1, 16))

    documento.build(elementos)
    return archivo.getvalue()


@never_cache
@api_view(["GET"])
@requiere_permiso("reportes.exportar")
def export_report(request, tipo, formato):
    if formato not in ("pdf", "xlsx"):
        raise serializers.ValidationError({
            "formato": "Formato no válido."
        })

    datos = datos_para_exportar(request, tipo)

    if not datos["hay_datos"]:
        raise serializers.ValidationError({
            "detail": "No hay datos disponibles para exportar."
        })

    if formato == "pdf":
        contenido = generar_pdf(datos, request.user)
        tipo_archivo = "application/pdf"
    else:
        contenido = generar_excel(datos, request.user)
        tipo_archivo = (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

    nombre = f"SIAM_{tipo}_{timezone.localdate().isoformat()}.{formato}"

    respuesta = HttpResponse(
        contenido,
        content_type=tipo_archivo,
    )
    respuesta["Content-Disposition"] = (
        f'attachment; filename="{nombre}"'
    )

    return respuesta
