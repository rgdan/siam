
<script setup>
import { computed, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { locale } = useI18n({ useScope: "global" })

const fechaInicio = ref("")
const fechaFin = ref("")
const reporte = ref(null)
const cargando = ref(false)
const error = ref("")
const filtroAplicado = ref(false)

const descargando = ref("")
const errorExportacion = ref("")

const textos = {
  es: {
    titulo: "Reportes consolidados",
    descripcion: "Resumen general de visitantes, eventos y colecciones del museo.",
    filtros: "Período del reporte",
    inicio: "Fecha inicial",
    fin: "Fecha final",
    generar: "Generar reporte",
    limpiar: "Mes actual",
    cargando: "Cargando información...",
    error: "No se pudo cargar el reporte. Intentá nuevamente.",
    fechasInvalidas: "La fecha final no puede ser anterior a la inicial.",
    sinDatos: "Sin datos para el período",
    visitantes: "Visitantes",
    totalIngresos: "Total de ingresos",
    nacionalidad: "Por nacionalidad",
    nacional: "Nacionales",
    extranjero: "Extranjeros",
    sexo: "Por sexo",
    masculino: "Masculino",
    femenino: "Femenino",
    edad: "Por rango de edad",
    mayor: "Mayores",
    menor: "Menores",
    eventos: "Eventos",
    totalEventos: "Total de eventos",
    publicos: "Públicos",
    privados: "Privados",
    cancelados: "Cancelados",
    asistencia: "Asistencia de eventos finalizados",
    finalizados: "Eventos finalizados",
    conRegistro: "Con asistencia registrada",
    sinRegistro: "Sin asistencia registrada",
    esperados: "Asistentes esperados",
    reales: "Asistentes reales",
    cumplimiento: "Cumplimiento",
    colecciones: "Colecciones",
    totalPiezas: "Total de piezas",
    activas: "Piezas activas",
    estados: "Piezas por estado",
    displayed: "En exhibición",
    stored: "Almacenadas",
    loaned: "En préstamo",
    missing: "Robadas o extraviadas",
    decommissioned: "Dadas de baja",
    porTipo: "Por tipo de objeto",
    porColeccion: "Por colección",
    sinAsignar: "Sin asignar",
    generado: "Generado",
    periodo: "Período",
    todasFechas: "Todas las fechas",
    nota:
      "La asistencia esperada y real considera únicamente eventos finalizados con asistencia registrada. Los eventos sin registro no participan en esos totales.",
    noCumplimiento: "Sin registro",

    exportar: "Exportar reporte consolidado",
    descargarPdf: "Descargar PDF",
    descargarExcel: "Descargar Excel",
    descargando: "Generando archivo...",
    errorDescarga: "No se pudo descargar el archivo. Intentá nuevamente.",
    sinDatosExportar: "No hay información disponible para exportar.",

    exportarAsistencia: "Exportar reporte de asistencia",
    pdfAsistencia: "Descargar PDF de asistencia",
    excelAsistencia: "Descargar Excel de asistencia",
    sinAsistencia:
      "No hay eventos finalizados en este período para exportar.",
  },

  en: {
    titulo: "Consolidated reports",
    descripcion: "General overview of museum visitors, events and collections.",
    filtros: "Report period",
    inicio: "Start date",
    fin: "End date",
    generar: "Generate report",
    limpiar: "Current month",
    cargando: "Loading information...",
    error: "The report could not be loaded. Please try again.",
    fechasInvalidas: "The end date cannot be before the start date.",
    sinDatos: "No data for the selected period",
    visitantes: "Visitors",
    totalIngresos: "Total entries",
    nacionalidad: "By nationality",
    nacional: "National",
    extranjero: "Foreign",
    sexo: "By sex",
    masculino: "Male",
    femenino: "Female",
    edad: "By age group",
    mayor: "Adults",
    menor: "Minors",
    eventos: "Events",
    totalEventos: "Total events",
    publicos: "Public",
    privados: "Private",
    cancelados: "Cancelled",
    asistencia: "Attendance at finished events",
    finalizados: "Finished events",
    conRegistro: "With recorded attendance",
    sinRegistro: "Without recorded attendance",
    esperados: "Expected attendees",
    reales: "Actual attendees",
    cumplimiento: "Attendance rate",
    colecciones: "Collections",
    totalPiezas: "Total pieces",
    activas: "Active pieces",
    estados: "Pieces by status",
    displayed: "On display",
    stored: "Stored",
    loaned: "On loan",
    missing: "Stolen or missing",
    decommissioned: "Decommissioned",
    porTipo: "By object type",
    porColeccion: "By collection",
    sinAsignar: "Unassigned",
    generado: "Generated",
    periodo: "Period",
    todasFechas: "All dates",
    nota:
      "Expected and actual attendance includes only finished events with recorded attendance. Events without attendance records are excluded from these totals.",
    noCumplimiento: "Not recorded",

    exportar: "Export consolidated report",
    descargarPdf: "Download PDF",
    descargarExcel: "Download Excel",
    descargando: "Generating file...",
    errorDescarga: "The file could not be downloaded. Please try again.",
    sinDatosExportar: "No information is available for export.",

    exportarAsistencia: "Export attendance report",
    pdfAsistencia: "Download attendance PDF",
    excelAsistencia: "Download attendance Excel",
    sinAsistencia:
      "There are no completed events in this period to export.",
  },
}

function traducir(clave) {
  return textos[locale.value === "en" ? "en" : "es"][clave] || clave
}

function numero(valor) {
  return new Intl.NumberFormat(
    locale.value === "en" ? "en-US" : "es-CR"
  ).format(valor ?? 0)
}

function porcentaje(valor) {
  if (valor === null || valor === undefined) {
    return traducir("noCumplimiento")
  }

  return `${new Intl.NumberFormat(
    locale.value === "en" ? "en-US" : "es-CR",
    { maximumFractionDigits: 2 }
  ).format(valor)} %`
}

function fechaLegible(valor) {
  if (!valor) return traducir("todasFechas")

  const [anio, mes, dia] = valor.split("-").map(Number)

  return new Intl.DateTimeFormat(
    locale.value === "en" ? "en-US" : "es-CR",
    { day: "2-digit", month: "long", year: "numeric" }
  ).format(new Date(anio, mes - 1, dia))
}

function fechaGeneracion(valor) {
  if (!valor) return ""

  return new Intl.DateTimeFormat(
    locale.value === "en" ? "en-US" : "es-CR",
    { dateStyle: "medium", timeStyle: "short" }
  ).format(new Date(valor))
}

// Indica si existe información para exportar el reporte general.
const hayDatos = computed(() => {
  if (!reporte.value) return false

  return (
    reporte.value.visitantes.total > 0 ||
    reporte.value.eventos.total > 0 ||
    reporte.value.colecciones.total > 0
  )
})

// Indica si existen eventos finalizados para exportar asistencia.
const hayDatosAsistencia = computed(() => {
  return (
    (reporte.value?.eventos?.asistencia?.eventos_finalizados ?? 0) > 0
  )
})

// Utiliza las fechas del último reporte generado.
function parametrosReporte() {
  const parametros = new URLSearchParams()

  const inicio = reporte.value?.filtros?.fecha_inicio
  const fin = reporte.value?.filtros?.fecha_fin

  if (inicio) parametros.set("fecha_inicio", inicio)
  if (fin) parametros.set("fecha_fin", fin)

  return parametros.toString()
}

// SIAM-29: descarga PDF o Excel del reporte solicitado.
async function descargarReporte(tipo, formato) {
  if (cargando.value || descargando.value || !reporte.value) return

  if (!["consolidated", "attendance"].includes(tipo)) return
  if (!["pdf", "xlsx"].includes(formato)) return

  if (tipo === "consolidated" && !hayDatos.value) return
  if (tipo === "attendance" && !hayDatosAsistencia.value) return

  descargando.value = `${tipo}-${formato}`
  errorExportacion.value = ""

  try {
    const parametros = parametrosReporte()

    const ruta =
      `reports/export/${tipo}/${formato}/` +
      (parametros ? `?${parametros}` : "")

    const respuesta = await solicitar(ruta)

    if (respuesta.status === 401) {
      reporte.value = null
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      reporte.value = null
      emit("sin-acceso")
      return
    }

    if (!respuesta.ok) {
      throw new Error("No se pudo generar el archivo")
    }

    const archivo = await respuesta.blob()

    if (!archivo.size) {
      throw new Error("El archivo está vacío")
    }

    const urlTemporal = URL.createObjectURL(archivo)
    const enlace = document.createElement("a")

    enlace.href = urlTemporal
    enlace.download =
      `SIAM_${tipo}_${new Date().toISOString().slice(0, 10)}.${formato}`

    document.body.appendChild(enlace)
    enlace.click()
    enlace.remove()

    setTimeout(() => {
      URL.revokeObjectURL(urlTemporal)
    }, 1000)
  } catch {
    errorExportacion.value = "error"
  } finally {
    descargando.value = ""
  }
}

async function generarReporte() {
  if (cargando.value || descargando.value) return

  if (
    fechaInicio.value &&
    fechaFin.value &&
    fechaInicio.value > fechaFin.value
  ) {
    error.value = "fechas"
    return
  }

  cargando.value = true
  error.value = ""
  errorExportacion.value = ""

  try {
    const parametros = new URLSearchParams()

    if (filtroAplicado.value) {
      if (fechaInicio.value) {
        parametros.set("fecha_inicio", fechaInicio.value)
      }

      if (fechaFin.value) {
        parametros.set("fecha_fin", fechaFin.value)
      }
    }

    const consulta = parametros.toString()

    const ruta =
      `reports/consolidated/` +
      (consulta ? `?${consulta}` : "")

    const respuesta = await solicitar(ruta)

    if (respuesta.status === 401) {
      reporte.value = null
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      reporte.value = null
      emit("sin-acceso")
      return
    }

    if (!respuesta.ok) {
      throw new Error("Error al consultar el reporte")
    }

    reporte.value = await respuesta.json()
  } catch {
    reporte.value = null
    error.value = "general"
  } finally {
    cargando.value = false
  }
}

function aplicarFiltros() {
  filtroAplicado.value = true
  generarReporte()
}

function restablecerFiltros() {
  fechaInicio.value = ""
  fechaFin.value = ""
  filtroAplicado.value = false
  generarReporte()
}

function nombreCategoria(nombre) {
  return nombre || traducir("sinAsignar")
}

onMounted(generarReporte)
</script>

<template>
  <div class="reporte-consolidado">
    <header class="encabezado-reporte">
      <h1>{{ traducir("titulo") }}</h1>
      <p>{{ traducir("descripcion") }}</p>
    </header>

    <form class="panel-filtros" @submit.prevent="aplicarFiltros">
      <h2>{{ traducir("filtros") }}</h2>

      <div class="fila-filtros">
        <div class="campo">
          <label for="consolidado-fecha-inicio">
            {{ traducir("inicio") }}
          </label>
          <input
            id="consolidado-fecha-inicio"
            v-model="fechaInicio"
            type="date"
            :disabled="cargando || Boolean(descargando)"
          />
        </div>

        <div class="campo">
          <label for="consolidado-fecha-fin">
            {{ traducir("fin") }}
          </label>
          <input
            id="consolidado-fecha-fin"
            v-model="fechaFin"
            type="date"
            :disabled="cargando || Boolean(descargando)"
          />
        </div>

        <button
          type="submit"
          :disabled="cargando || Boolean(descargando)"
        >
          {{ traducir("generar") }}
        </button>

        <button
          type="button"
          class="boton-secundario"
          :disabled="cargando || Boolean(descargando)"
          @click="restablecerFiltros"
        >
          {{ traducir("limpiar") }}
        </button>
      </div>
    </form>

    <p v-if="cargando" role="status">
      {{ traducir("cargando") }}
    </p>

    <p v-if="error" class="mensaje-error" role="alert">
      {{
        error === "fechas"
          ? traducir("fechasInvalidas")
          : traducir("error")
      }}
    </p>

    <template v-if="reporte">
      <div class="informacion-periodo">
        <p>
          <strong>{{ traducir("periodo") }}:</strong>
          {{ fechaLegible(reporte.filtros.fecha_inicio) }}
          —
          {{ fechaLegible(reporte.filtros.fecha_fin) }}
        </p>

        <p>
          <strong>{{ traducir("generado") }}:</strong>
          {{ fechaGeneracion(reporte.fecha_generacion) }}
        </p>
      </div>

      <!-- SIAM-29: exportación del reporte consolidado -->
      <section class="panel-exportacion">
        <h2>{{ traducir("exportar") }}</h2>

        <div class="botones-exportacion">
          <button
            type="button"
            :disabled="!hayDatos || cargando || Boolean(descargando)"
            @click="descargarReporte('consolidated', 'pdf')"
          >
            {{
              descargando === "consolidated-pdf"
                ? traducir("descargando")
                : traducir("descargarPdf")
            }}
          </button>

          <button
            type="button"
            :disabled="!hayDatos || cargando || Boolean(descargando)"
            @click="descargarReporte('consolidated', 'xlsx')"
          >
            {{
              descargando === "consolidated-xlsx"
                ? traducir("descargando")
                : traducir("descargarExcel")
            }}
          </button>
        </div>

        <p v-if="!hayDatos" class="ayuda-exportacion">
          {{ traducir("sinDatosExportar") }}
        </p>
      </section>

      <!-- Visitantes -->
      <section class="seccion-reporte">
        <h2>{{ traducir("visitantes") }}</h2>

        <p
          v-if="reporte.visitantes.total === 0"
          class="mensaje-vacio"
        >
          {{ traducir("sinDatos") }}
        </p>

        <template v-else>
          <div class="tarjetas">
            <article class="tarjeta tarjeta-destacada">
              <h3>{{ traducir("totalIngresos") }}</h3>
              <p>{{ numero(reporte.visitantes.total) }}</p>
            </article>
          </div>

          <div class="grupos">
            <article class="grupo-estadisticas">
              <h3>{{ traducir("nacionalidad") }}</h3>
              <dl>
                <div>
                  <dt>{{ traducir("nacional") }}</dt>
                  <dd>{{ numero(reporte.visitantes.por_nacionalidad.nacional) }}</dd>
                </div>
                <div>
                  <dt>{{ traducir("extranjero") }}</dt>
                  <dd>{{ numero(reporte.visitantes.por_nacionalidad.extranjero) }}</dd>
                </div>
              </dl>
            </article>

            <article class="grupo-estadisticas">
              <h3>{{ traducir("sexo") }}</h3>
              <dl>
                <div>
                  <dt>{{ traducir("masculino") }}</dt>
                  <dd>{{ numero(reporte.visitantes.por_sexo.masculino) }}</dd>
                </div>
                <div>
                  <dt>{{ traducir("femenino") }}</dt>
                  <dd>{{ numero(reporte.visitantes.por_sexo.femenino) }}</dd>
                </div>
              </dl>
            </article>

            <article class="grupo-estadisticas">
              <h3>{{ traducir("edad") }}</h3>
              <dl>
                <div>
                  <dt>{{ traducir("mayor") }}</dt>
                  <dd>{{ numero(reporte.visitantes.por_edad.mayor) }}</dd>
                </div>
                <div>
                  <dt>{{ traducir("menor") }}</dt>
                  <dd>{{ numero(reporte.visitantes.por_edad.menor) }}</dd>
                </div>
              </dl>
            </article>
          </div>
        </template>
      </section>

      <!-- Eventos -->
      <section class="seccion-reporte">
        <h2>{{ traducir("eventos") }}</h2>

        <p
          v-if="reporte.eventos.total === 0"
          class="mensaje-vacio"
        >
          {{ traducir("sinDatos") }}
        </p>

        <template v-else>
          <div class="tarjetas">
            <article class="tarjeta tarjeta-destacada">
              <h3>{{ traducir("totalEventos") }}</h3>
              <p>{{ numero(reporte.eventos.total) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("publicos") }}</h3>
              <p>{{ numero(reporte.eventos.publicos) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("privados") }}</h3>
              <p>{{ numero(reporte.eventos.privados) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("cancelados") }}</h3>
              <p>{{ numero(reporte.eventos.cancelados) }}</p>
            </article>
          </div>

          <h3 class="subtitulo">
            {{ traducir("asistencia") }}
          </h3>

          <div class="tarjetas">
            <article class="tarjeta">
              <h3>{{ traducir("finalizados") }}</h3>
              <p>{{ numero(reporte.eventos.asistencia.eventos_finalizados) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("conRegistro") }}</h3>
              <p>{{ numero(reporte.eventos.asistencia.eventos_con_registro) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("sinRegistro") }}</h3>
              <p>{{ numero(reporte.eventos.asistencia.eventos_sin_registro) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("esperados") }}</h3>
              <p>{{ numero(reporte.eventos.asistencia.asistentes_esperados) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("reales") }}</h3>
              <p>{{ numero(reporte.eventos.asistencia.asistentes_reales) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("cumplimiento") }}</h3>
              <p class="valor-porcentaje">
                {{ porcentaje(reporte.eventos.asistencia.cumplimiento_porcentaje) }}
              </p>
            </article>
          </div>

          <p class="nota-reporte">
            {{ traducir("nota") }}
          </p>

          <!-- SIAM-29: exportación de asistencia -->
          <section class="panel-exportacion exportacion-asistencia">
            <h3>{{ traducir("exportarAsistencia") }}</h3>

            <div class="botones-exportacion">
              <button
                type="button"
                :disabled="!hayDatosAsistencia || cargando || Boolean(descargando)"
                @click="descargarReporte('attendance', 'pdf')"
              >
                {{
                  descargando === "attendance-pdf"
                    ? traducir("descargando")
                    : traducir("pdfAsistencia")
                }}
              </button>

              <button
                type="button"
                :disabled="!hayDatosAsistencia || cargando || Boolean(descargando)"
                @click="descargarReporte('attendance', 'xlsx')"
              >
                {{
                  descargando === "attendance-xlsx"
                    ? traducir("descargando")
                    : traducir("excelAsistencia")
                }}
              </button>
            </div>

            <p v-if="!hayDatosAsistencia" class="ayuda-exportacion">
              {{ traducir("sinAsistencia") }}
            </p>
          </section>
        </template>
      </section>

      <!-- Colecciones -->
      <section class="seccion-reporte">
        <h2>{{ traducir("colecciones") }}</h2>

        <p
          v-if="reporte.colecciones.total === 0"
          class="mensaje-vacio"
        >
          {{ traducir("sinDatos") }}
        </p>

        <template v-else>
          <div class="tarjetas">
            <article class="tarjeta tarjeta-destacada">
              <h3>{{ traducir("totalPiezas") }}</h3>
              <p>{{ numero(reporte.colecciones.total) }}</p>
            </article>
            <article class="tarjeta">
              <h3>{{ traducir("activas") }}</h3>
              <p>{{ numero(reporte.colecciones.active) }}</p>
            </article>
          </div>

          <div class="grupos">
            <article class="grupo-estadisticas">
              <h3>{{ traducir("estados") }}</h3>
              <dl>
                <div
                  v-for="(cantidad, estado) in reporte.colecciones.by_state"
                  :key="estado"
                >
                  <dt>{{ traducir(estado) }}</dt>
                  <dd>{{ numero(cantidad) }}</dd>
                </div>
              </dl>
            </article>

            <article class="grupo-estadisticas">
              <h3>{{ traducir("porTipo") }}</h3>
              <dl>
                <div
                  v-for="(cantidad, tipo) in reporte.colecciones.by_object_type"
                  :key="tipo"
                >
                  <dt>{{ nombreCategoria(tipo) }}</dt>
                  <dd>{{ numero(cantidad) }}</dd>
                </div>
              </dl>
            </article>

            <article class="grupo-estadisticas">
              <h3>{{ traducir("porColeccion") }}</h3>
              <dl>
                <div
                  v-for="(cantidad, coleccion) in reporte.colecciones.by_collection"
                  :key="coleccion"
                >
                  <dt>{{ nombreCategoria(coleccion) }}</dt>
                  <dd>{{ numero(cantidad) }}</dd>
                </div>
              </dl>
            </article>
          </div>
        </template>
      </section>
    </template>

    <p v-if="errorExportacion" class="mensaje-error" role="alert">
      {{ traducir("errorDescarga") }}
    </p>
  </div>
</template>

<style scoped>
.reporte-consolidado {
  width: 100%;
  min-width: 0;
  color: var(--color-texto);
}

.encabezado-reporte h1 {
  margin: 0 0 12px;
  color: var(--color-enlace);
}

.encabezado-reporte p {
  margin: 0 0 24px;
  line-height: 1.5;
}

.panel-filtros,
.seccion-reporte,
.panel-exportacion {
  border: 1px solid var(--color-borde);
  border-radius: 9px;
  padding: 20px;
  background: var(--color-control);
}

.panel-filtros h2,
.panel-exportacion h2,
.panel-exportacion h3 {
  margin: 0 0 16px;
  font-size: 17px;
}

.fila-filtros {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 12px;
}

.campo {
  display: grid;
  flex: 1 1 180px;
  gap: 7px;
  min-width: 0;
}

.campo label {
  font-size: 14px;
  font-weight: 600;
}

.campo input,
.fila-filtros button,
.botones-exportacion button {
  box-sizing: border-box;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  font: inherit;
}

.campo input {
  width: 100%;
  min-width: 0;
  background: var(--color-control);
  color: var(--color-texto);
}

.fila-filtros button,
.botones-exportacion button {
  background: var(--color-header);
  color: #ffffff;
  cursor: pointer;
}

.fila-filtros .boton-secundario {
  background: transparent;
  color: var(--color-texto);
}

.fila-filtros button:disabled,
.botones-exportacion button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.informacion-periodo {
  margin: 20px 0;
  overflow-wrap: anywhere;
  font-size: 13px;
}

.informacion-periodo p {
  margin: 5px 0;
}

.panel-exportacion {
  margin-bottom: 20px;
}

.botones-exportacion {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.botones-exportacion button {
  flex: 1 1 160px;
}

.ayuda-exportacion {
  margin: 12px 0 0;
  font-size: 13px;
}

.seccion-reporte {
  margin-bottom: 20px;
}

.seccion-reporte > h2 {
  margin: 0 0 20px;
  color: var(--color-enlace);
}

.tarjetas {
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, 190px), 1fr)
  );
  gap: 12px;
  margin-bottom: 18px;
}

.tarjeta,
.grupo-estadisticas {
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--color-borde);
  border-radius: 8px;
  background: var(--color-control);
}

.tarjeta h3 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 500;
}

.tarjeta p {
  margin: 0;
  color: var(--color-enlace);
  font-size: 27px;
  font-weight: 700;
}

.tarjeta .valor-porcentaje {
  font-size: 22px;
}

.tarjeta-destacada {
  border-width: 2px;
}

.grupos {
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, 240px), 1fr)
  );
  gap: 14px;
}

.grupo-estadisticas h3 {
  margin: 0 0 14px;
  font-size: 16px;
}

.grupo-estadisticas dl {
  margin: 0;
}

.grupo-estadisticas dl > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-borde);
}

.grupo-estadisticas dl > div:last-child {
  border-bottom: 0;
}

.grupo-estadisticas dt {
  overflow-wrap: anywhere;
}

.grupo-estadisticas dd {
  margin: 0;
  font-weight: 700;
}

.subtitulo {
  margin: 24px 0 14px;
  font-size: 17px;
}

.mensaje-vacio {
  margin: 0;
  padding: 16px;
  border: 1px dashed var(--color-borde);
  border-radius: 7px;
}

.mensaje-error {
  color: var(--color-error);
}

.nota-reporte {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.6;
}

.exportacion-asistencia {
  margin: 20px 0 0;
}

@media (max-width: 600px) {
  .panel-filtros,
  .seccion-reporte,
  .panel-exportacion {
    padding: 14px;
  }

  .fila-filtros {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .fila-filtros button,
  .botones-exportacion button {
    width: 100%;
  }

  .botones-exportacion {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .tarjetas,
  .grupos {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
