
<script setup>
import { computed, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import { formatearFecha } from "../i18n/index.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { locale } = useI18n({ useScope: "global" })

const textos = {
  es: {
    titulo: "Reporte comparativo de asistencia",
    descripcion: "Compare la asistencia esperada y real de los eventos finalizados del museo.",
    fechaInicio: "Fecha inicial",
    fechaFin: "Fecha final",
    generar: "Generar reporte",
    limpiar: "Quitar filtros",
    cargando: "Generando reporte...",
    error: "No se pudo generar el reporte.",
    sinEventos: "No hay eventos para el rango seleccionado",
    fechaInvalida: "La fecha final no puede ser anterior a la fecha inicial.",
    evento: "Evento",
    fecha: "Fecha",
    tipo: "Tipo",
    esperados: "Asistentes esperados",
    reales: "Asistentes reales",
    cumplimiento: "Cumplimiento",
    total: "Total",
    publico: "Público",
    privado: "Privado",
    sinRegistro: "Sin registro",
    eventosMostrados: "Eventos mostrados",
    conRegistro: "Con asistencia registrada",
    sinRegistroCantidad: "Pendientes de registrar",
    nota: "Los eventos sin asistencia registrada aparecen en el reporte, pero no participan en los totales ni en el cumplimiento general.",
    sinFiltro: "Todos los eventos finalizados",
    desde: "Desde",
    hasta: "Hasta",
  },
  en: {
    titulo: "Attendance comparison report",
    descripcion: "Compare expected and actual attendance for completed museum events.",
    fechaInicio: "Start date",
    fechaFin: "End date",
    generar: "Generate report",
    limpiar: "Clear filters",
    cargando: "Generating report...",
    error: "The report could not be generated.",
    sinEventos: "No events found for the selected date range",
    fechaInvalida: "The end date cannot be earlier than the start date.",
    evento: "Event",
    fecha: "Date",
    tipo: "Type",
    esperados: "Expected attendees",
    reales: "Actual attendees",
    cumplimiento: "Fulfilment",
    total: "Total",
    publico: "Public",
    privado: "Private",
    sinRegistro: "Not recorded",
    eventosMostrados: "Events displayed",
    conRegistro: "Attendance recorded",
    sinRegistroCantidad: "Pending attendance",
    nota: "Events without recorded attendance are displayed but excluded from totals and overall fulfilment.",
    sinFiltro: "All completed events",
    desde: "From",
    hasta: "To",
  },
}

const texto = computed(() =>
  textos[locale.value === "en" ? "en" : "es"]
)

const idiomaRegional = computed(() =>
  locale.value === "en" ? "en-US" : "es-CR"
)

const fechaInicio = ref("")
const fechaFin = ref("")
const cargando = ref(false)
const error = ref("")
const reporte = ref(null)
const filtrosAplicados = ref({
  fecha_inicio: null,
  fecha_fin: null,
})

const eventos = computed(() =>
  Array.isArray(reporte.value?.eventos)
    ? reporte.value.eventos
    : []
)

const totales = computed(() =>
  reporte.value?.totales ?? {
    asistentes_esperados: 0,
    asistentes_reales: 0,
    cumplimiento_porcentaje: null,
  }
)

const resumen = computed(() =>
  reporte.value?.resumen ?? {
    eventos_mostrados: 0,
    eventos_con_registro: 0,
    eventos_sin_registro: 0,
  }
)

const periodoAplicado = computed(() => {
  const inicio = filtrosAplicados.value.fecha_inicio
  const fin = filtrosAplicados.value.fecha_fin

  if (!inicio && !fin) return texto.value.sinFiltro

  const partes = []

  if (inicio) partes.push(`${texto.value.desde}: ${inicio}`)
  if (fin) partes.push(`${texto.value.hasta}: ${fin}`)

  return partes.join(" · ")
})

function porcentaje(valor) {
  if (valor === null || valor === undefined) {
    return "—"
  }

  const numero = Number(valor)

  if (!Number.isFinite(numero)) return "—"

  return (
    new Intl.NumberFormat(idiomaRegional.value, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(numero) + " %"
  )
}

function numero(valor) {
  return new Intl.NumberFormat(idiomaRegional.value).format(
    Number(valor ?? 0)
  )
}

function tipoEvento(tipo) {
  return tipo === "privado"
    ? texto.value.privado
    : texto.value.publico
}

function asistenciaReal(evento) {
  if (
    evento.asistentes_reales === null ||
    evento.asistentes_reales === undefined
  ) {
    return texto.value.sinRegistro
  }

  return numero(evento.asistentes_reales)
}

async function obtenerError(respuesta) {
  try {
    const datos = await respuesta.json()

    if (typeof datos.detail === "string") {
      return datos.detail
    }

    const mensajes = Object.values(datos)
      .flat()
      .filter(valor => typeof valor === "string")

    return mensajes[0] || texto.value.error
  } catch {
    return texto.value.error
  }
}

async function generarReporte() {
  if (cargando.value) return

  error.value = ""

  if (
    fechaInicio.value &&
    fechaFin.value &&
    fechaInicio.value > fechaFin.value
  ) {
    error.value = texto.value.fechaInvalida
    return
  }

  cargando.value = true

  try {
    const parametros = new URLSearchParams()

    if (fechaInicio.value) {
      parametros.set("fecha_inicio", fechaInicio.value)
    }

    if (fechaFin.value) {
      parametros.set("fecha_fin", fechaFin.value)
    }

    const consulta = parametros.toString()
    const ruta = `reports/attendance/${consulta ? `?${consulta}` : ""}`

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
      throw new Error(await obtenerError(respuesta))
    }

    const datos = await respuesta.json()

    if (
      !Array.isArray(datos.eventos) ||
      !datos.totales ||
      !datos.resumen
    ) {
      throw new Error(texto.value.error)
    }

    reporte.value = datos
    filtrosAplicados.value = {
      fecha_inicio: datos.filtros?.fecha_inicio ?? null,
      fecha_fin: datos.filtros?.fecha_fin ?? null,
    }
  } catch (fallo) {
    reporte.value = null
    error.value = fallo.message || texto.value.error
  } finally {
    cargando.value = false
  }
}

async function limpiarFiltros() {
  fechaInicio.value = ""
  fechaFin.value = ""
  await generarReporte()
}

onMounted(generarReporte)
</script>

<template>
  <section class="reporte-asistencia">
    <header class="encabezado">
      <h2>{{ texto.titulo }}</h2>
      <p>{{ texto.descripcion }}</p>
    </header>

    <form class="filtros" @submit.prevent="generarReporte">
      <div class="campo">
        <label for="reporte-fecha-inicio">
          {{ texto.fechaInicio }}
        </label>

        <input
          id="reporte-fecha-inicio"
          v-model="fechaInicio"
          type="date"
          :disabled="cargando"
        />
      </div>

      <div class="campo">
        <label for="reporte-fecha-fin">
          {{ texto.fechaFin }}
        </label>

        <input
          id="reporte-fecha-fin"
          v-model="fechaFin"
          type="date"
          :disabled="cargando"
        />
      </div>

      <div class="acciones-filtros">
        <button type="submit" :disabled="cargando">
          {{ texto.generar }}
        </button>

        <button
          type="button"
          class="boton-secundario"
          :disabled="cargando"
          @click="limpiarFiltros"
        >
          {{ texto.limpiar }}
        </button>
      </div>
    </form>

    <p v-if="error" class="mensaje-error" role="alert">
      {{ error }}
    </p>

    <p v-if="cargando" role="status">
      {{ texto.cargando }}
    </p>

    <template v-else-if="reporte">
      <p class="periodo">
        {{ periodoAplicado }}
      </p>

      <div v-if="eventos.length === 0" class="sin-datos" role="status">
        {{ texto.sinEventos }}
      </div>

      <template v-else>
        <div class="resumen">
          <div class="tarjeta-resumen">
            <span>{{ texto.eventosMostrados }}</span>
            <strong>{{ numero(resumen.eventos_mostrados) }}</strong>
          </div>

          <div class="tarjeta-resumen">
            <span>{{ texto.conRegistro }}</span>
            <strong>{{ numero(resumen.eventos_con_registro) }}</strong>
          </div>

          <div class="tarjeta-resumen">
            <span>{{ texto.sinRegistroCantidad }}</span>
            <strong>{{ numero(resumen.eventos_sin_registro) }}</strong>
          </div>
        </div>

        <div class="tabla-contenedor" tabindex="0" role="region" :aria-label="texto.titulo">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ texto.fecha }}</th>
                <th scope="col">{{ texto.evento }}</th>
                <th scope="col">{{ texto.tipo }}</th>
                <th scope="col" class="numero">{{ texto.esperados }}</th>
                <th scope="col" class="numero">{{ texto.reales }}</th>
                <th scope="col" class="numero">{{ texto.cumplimiento }}</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="evento in eventos" :key="evento.id">
                <td>{{ formatearFecha(evento.fecha) }}</td>
                <td>{{ evento.descripcion }}</td>
                <td>{{ tipoEvento(evento.tipo) }}</td>
                <td class="numero">{{ numero(evento.asistentes_esperados) }}</td>
                <td class="numero">{{ asistenciaReal(evento) }}</td>
                <td class="numero">
                  {{ porcentaje(evento.cumplimiento_porcentaje) }}
                </td>
              </tr>
            </tbody>

            <tfoot>
              <tr>
                <th scope="row" colspan="3">{{ texto.total }}</th>
                <td class="numero">{{ numero(totales.asistentes_esperados) }}</td>
                <td class="numero">{{ numero(totales.asistentes_reales) }}</td>
                <td class="numero">
                  {{ porcentaje(totales.cumplimiento_porcentaje) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <p class="nota">
          {{ texto.nota }}
        </p>
      </template>
    </template>
  </section>
</template>

<style scoped>
.reporte-asistencia {
  width: 100%;
  max-width: 1180px;
  min-width: 0;
  margin: 0 auto;
  color: var(--color-texto);
}

.encabezado h2 {
  margin-top: 0;
  color: var(--color-enlace);
}

.encabezado p {
  line-height: 1.6;
}

.filtros {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 16px;
  margin: 24px 0;
  padding: 20px;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-control);
}

.campo {
  flex: 1 1 180px;
  display: grid;
  gap: 8px;
  min-width: 0;
}

.campo label {
  font-weight: 600;
}

.campo input {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  background: var(--color-control);
  color: var(--color-texto);
  font: inherit;
}

.acciones-filtros {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

button {
  min-height: 44px;
  padding: 10px 16px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  background: var(--color-header);
  color: #ffffff;
  font: inherit;
  cursor: pointer;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.boton-secundario {
  background: var(--color-control);
  color: var(--color-texto);
}

.periodo {
  margin: 20px 0;
  color: var(--color-enlace);
  font-weight: 600;
}

.resumen {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 20px 0;
}

.tarjeta-resumen {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--color-borde);
  border-radius: 8px;
  background: var(--color-control);
}

.tarjeta-resumen span {
  line-height: 1.4;
}

.tarjeta-resumen strong {
  font-size: 1.4rem;
  color: var(--color-enlace);
}

.tabla-contenedor {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-control);
}

table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
  text-align: left;
}

th, td {
  padding: 14px 12px;
  border-bottom: 1px solid var(--color-borde);
  overflow-wrap: anywhere;
}

thead th {
  background: var(--color-header);
  color: #ffffff;
}

.numero {
  text-align: right;
  white-space: nowrap;
}

tfoot tr {
  background: var(--color-control);
  font-weight: 700;
}

tfoot th,
tfoot td {
  border-top: 2px solid var(--color-borde);
  border-bottom: none;
}

.sin-datos {
  padding: 24px;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-control);
}

.nota {
  margin-top: 16px;
  line-height: 1.6;
  font-size: 0.9rem;
}

.mensaje-error {
  color: var(--color-error);
}

@media (max-width: 767px) {
  .filtros {
    padding: 12px;
  }

  .resumen {
    grid-template-columns: 1fr;
  }

  .acciones-filtros,
  .acciones-filtros button {
    width: 100%;
  }
}
</style>
