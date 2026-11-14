
<script setup>
import { computed, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import { formatearFecha } from "../i18n/index.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t, te, locale } = useI18n({ useScope: "global" })

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

  if (!inicio && !fin) return t('attendanceReport.sinFiltro')

  const partes = []

  if (inicio) partes.push(`${t('attendanceReport.desde')}: ${inicio}`)
  if (fin) partes.push(`${t('attendanceReport.hasta')}: ${fin}`)

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
    ? t('attendanceReport.privado')
    : t('attendanceReport.publico')
}

function asistenciaReal(evento) {
  if (
    evento.asistentes_reales === null ||
    evento.asistentes_reales === undefined
  ) {
    return t('attendanceReport.sinRegistro')
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

    return mensajes[0] || 'attendanceReport.error'
  } catch {
    return 'attendanceReport.error'
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
    error.value = 'attendanceReport.fechaInvalida'
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
      throw new Error('attendanceReport.error')
    }

    reporte.value = datos
    filtrosAplicados.value = {
      fecha_inicio: datos.filtros?.fecha_inicio ?? null,
      fecha_fin: datos.filtros?.fecha_fin ?? null,
    }
  } catch (fallo) {
    reporte.value = null
    error.value = fallo.message || 'attendanceReport.error'
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
      <h2>{{ t('attendanceReport.titulo') }}</h2>
      <p>{{ t('attendanceReport.descripcion') }}</p>
    </header>

    <form class="filtros" @submit.prevent="generarReporte">
      <div class="campo">
        <label for="reporte-fecha-inicio">
          {{ t('attendanceReport.fechaInicio') }}
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
          {{ t('attendanceReport.fechaFin') }}
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
          {{ t('attendanceReport.generar') }}
        </button>

        <button
          type="button"
          class="boton-secundario"
          :disabled="cargando"
          @click="limpiarFiltros"
        >
          {{ t('attendanceReport.limpiar') }}
        </button>
      </div>
    </form>

    <p v-if="error" class="mensaje-error" role="alert">
      {{ te(error) ? t(error) : error }}
    </p>

    <p v-if="cargando" role="status">
      {{ t('attendanceReport.cargando') }}
    </p>

    <template v-else-if="reporte">
      <p class="periodo">
        {{ periodoAplicado }}
      </p>

      <div v-if="eventos.length === 0" class="sin-datos" role="status">
        {{ t('attendanceReport.sinEventos') }}
      </div>

      <template v-else>
        <div class="resumen">
          <div class="tarjeta-resumen">
            <span>{{ t('attendanceReport.eventosMostrados') }}</span>
            <strong>{{ numero(resumen.eventos_mostrados) }}</strong>
          </div>

          <div class="tarjeta-resumen">
            <span>{{ t('attendanceReport.conRegistro') }}</span>
            <strong>{{ numero(resumen.eventos_con_registro) }}</strong>
          </div>

          <div class="tarjeta-resumen">
            <span>{{ t('attendanceReport.sinRegistroCantidad') }}</span>
            <strong>{{ numero(resumen.eventos_sin_registro) }}</strong>
          </div>
        </div>

        <div class="tabla-contenedor" tabindex="0" role="region" :aria-label="t('attendanceReport.titulo')">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('attendanceReport.fecha') }}</th>
                <th scope="col">{{ t('attendanceReport.evento') }}</th>
                <th scope="col">{{ t('attendanceReport.tipo') }}</th>
                <th scope="col" class="numero">{{ t('attendanceReport.esperados') }}</th>
                <th scope="col" class="numero">{{ t('attendanceReport.reales') }}</th>
                <th scope="col" class="numero">{{ t('attendanceReport.cumplimiento') }}</th>
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
                <th scope="row" colspan="3">{{ t('attendanceReport.total') }}</th>
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
          {{ t('attendanceReport.nota') }}
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
