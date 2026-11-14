
<script setup>
import { computed, nextTick, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import { formatearFecha, formatearHora } from "../i18n/index.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t, te, locale } = useI18n({ useScope: "global" })

const idiomaRegional = computed(() =>
  locale.value === "en" ? "en-US" : "es-CR"
)

const eventos = ref([])
const cargando = ref(false)
const error = ref(false)

// SIAM-15: permisos y gestión de eventos.
const usuario = ref(null)
const procesando = ref(false)
const mensaje = ref("")
const errorOperacion = ref("")
const eventoEditando = ref(null)
const eventoCancelando = ref(null)

// SIAM-16: registro y corrección de asistencia de eventos pasados.
const eventoAsistencia = ref(null)
const cantidadAsistencia = ref("")
const panelGestion = ref(null)

const formulario = ref({
  fecha: "",
  descripcion: "",
  ubicacion: "",
  tipo: "publico",
  asistentes_esperados: 1,
})

const puedeEditar = computed(() =>
  usuario.value?.permissions?.includes("eventos.actualizar") === true
)

const puedeCancelar = computed(() =>
  usuario.value?.permissions?.includes("eventos.cancelar") === true
)

const puedeRegistrarAsistencia = computed(() =>
  usuario.value?.permissions?.includes("eventos.registrar_asistencia") === true
)

function esEventoPasado(evento) {
  return new Date(evento.fecha).getTime() <= Date.now()
}

function tieneAsistencia(evento) {
  return evento.asistentes_reales !== null &&
    evento.asistentes_reales !== undefined
}

function esEventoFuturo(evento) {
  return new Date(evento.fecha).getTime() > Date.now()
}

// SIAM-9 y SIAM-14: calendario mensual.
const hoy = new Date()
const mesActual = ref(new Date(hoy.getFullYear(), hoy.getMonth(), 1))
const diaSeleccionado = ref(
  new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
)

const tituloMes = computed(() => {
  const titulo = new Intl.DateTimeFormat(idiomaRegional.value, {
    month: "long",
    year: "numeric",
  }).format(mesActual.value)

  return titulo.charAt(0).toUpperCase() + titulo.slice(1)
})

const encabezadosSemana = computed(() =>
  Array.from({ length: 7 }, (_, indice) =>
    new Intl.DateTimeFormat(idiomaRegional.value, {
      weekday: "short",
    }).format(new Date(2024, 0, 1 + indice))
  )
)

function mismoDia(primera, segunda) {
  return (
    primera.getFullYear() === segunda.getFullYear() &&
    primera.getMonth() === segunda.getMonth() &&
    primera.getDate() === segunda.getDate()
  )
}

function eventosDelDia(fecha) {
  return eventos.value.filter(evento =>
    mismoDia(new Date(evento.fecha), fecha)
  )
}

const diasCalendario = computed(() => {
  const anio = mesActual.value.getFullYear()
  const mes = mesActual.value.getMonth()

  const primerDia = new Date(anio, mes, 1)
  const ultimoDia = new Date(anio, mes + 1, 0)
  const espaciosIniciales = (primerDia.getDay() + 6) % 7

  const dias = Array.from(
    { length: espaciosIniciales },
    () => null
  )

  for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
    dias.push(new Date(anio, mes, dia))
  }

  while (dias.length % 7 !== 0) {
    dias.push(null)
  }

  return dias
})

const eventosSeleccionados = computed(() =>
  eventosDelDia(diaSeleccionado.value)
)

const proximosEventos = computed(() =>
  eventos.value.filter(evento =>
    esEventoFuturo(evento)
  )
)

const tituloDiaSeleccionado = computed(() =>
  formatearFecha(diaSeleccionado.value)
)

function cambiarMes(cantidad) {
  const anio = mesActual.value.getFullYear()
  const mes = mesActual.value.getMonth()

  mesActual.value = new Date(anio, mes + cantidad, 1)

  diaSeleccionado.value = new Date(
    mesActual.value.getFullYear(),
    mesActual.value.getMonth(),
    1
  )
}

function seleccionarDia(fecha) {
  diaSeleccionado.value = new Date(
    fecha.getFullYear(),
    fecha.getMonth(),
    fecha.getDate()
  )
}

function volverHoy() {
  const actual = new Date()

  mesActual.value = new Date(
    actual.getFullYear(),
    actual.getMonth(),
    1
  )

  diaSeleccionado.value = new Date(
    actual.getFullYear(),
    actual.getMonth(),
    actual.getDate()
  )
}

function nombreTipo(tipo) {
  return tipo === "privado"
    ? t('internalEvents.privado')
    : t('internalEvents.publico')
}

// SIAM-15: lleva al usuario al formulario abierto.
async function mostrarPanelGestion() {
  await nextTick()

  panelGestion.value?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  })
}

// Obtiene la sesión y los permisos actuales.
async function cargarUsuario() {
  try {
    const respuesta = await solicitar("auth/me/")

    if (respuesta.status === 401) {
      usuario.value = null
      emit("sesion-expirada")
      return
    }

    if (!respuesta.ok) {
      usuario.value = null
      return
    }

    usuario.value = await respuesta.json()
  } catch {
    usuario.value = null
  }
}

// SIAM-14: consulta protegida de eventos internos.
async function cargarEventos() {
  if (cargando.value) return

  cargando.value = true
  error.value = false

  try {
    const respuesta = await solicitar("events/internal/")

    if (respuesta.status === 401) {
      eventos.value = []
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      eventos.value = []
      emit("sin-acceso")
      return
    }

    if (!respuesta.ok) {
      throw new Error("No se pudieron consultar los eventos.")
    }

    const datos = await respuesta.json()

    if (!Array.isArray(datos)) {
      throw new Error("La respuesta no contiene una lista de eventos.")
    }

    eventos.value = datos
      .filter(evento => {
        const fecha = new Date(evento.fecha).getTime()

        return (
          ["publico", "privado"].includes(evento.tipo) &&
          Number.isFinite(fecha)
        )
      })
      .sort((a, b) => new Date(a.fecha) - new Date(b.fecha))
  } catch {
    error.value = true
    eventos.value = []
  } finally {
    cargando.value = false
  }
}

// Convierte una fecha a formato local para datetime-local.
function fechaParaInput(valor) {
  const fecha = new Date(valor)

  if (Number.isNaN(fecha.getTime())) return ""

  const completar = numero => String(numero).padStart(2, "0")

  return (
    `${fecha.getFullYear()}-` +
    `${completar(fecha.getMonth() + 1)}-` +
    `${completar(fecha.getDate())}T` +
    `${completar(fecha.getHours())}:` +
    `${completar(fecha.getMinutes())}`
  )
}

// Obtiene el token CSRF desde Django.
async function obtenerCsrf() {
  const respuesta = await solicitar("auth/csrf/")

  if (!respuesta.ok) {
    throw new Error('internalEvents.errorOperacion')
  }

  const datos = await respuesta.json()

  if (!datos.csrfToken) {
    throw new Error('internalEvents.errorOperacion')
  }

  return datos.csrfToken
}

// Peticiones protegidas para gestionar eventos y asistencia.
async function solicitarGestion(ruta, metodo, datos) {
  const csrfToken = await obtenerCsrf()

  const baseApi = (
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000/api/"
  ).replace(/\/+$/, "")

  return fetch(`${baseApi}/${ruta}`, {
    method: metodo,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(datos),
  })
}

function limpiarOperacion() {
  mensaje.value = ""
  errorOperacion.value = ""
}

function cerrarEdicion() {
  eventoEditando.value = null
}

function cerrarCancelacion() {
  eventoCancelando.value = null
}

function cerrarAsistencia() {
  eventoAsistencia.value = null
  cantidadAsistencia.value = ""
}

// SIAM-16: abre el formulario de asistencia para eventos pasados.
async function iniciarAsistencia(evento) {
  if (
    !puedeRegistrarAsistencia.value ||
    !esEventoPasado(evento) ||
    procesando.value
  ) {
    return
  }

  limpiarOperacion()
  cerrarEdicion()
  cerrarCancelacion()

  eventoAsistencia.value = evento
  cantidadAsistencia.value = tieneAsistencia(evento)
    ? String(evento.asistentes_reales)
    : ""

  await mostrarPanelGestion()
}

// SIAM-16: registra o corrige los asistentes reales.
async function guardarAsistencia() {
  if (!eventoAsistencia.value || procesando.value) return

  limpiarOperacion()

  const entrada = String(cantidadAsistencia.value).trim()
  const cantidad = Number(entrada)

  if (
    !/^\d+$/.test(entrada) ||
    !Number.isSafeInteger(cantidad) ||
    cantidad > 2147483647
  ) {
    errorOperacion.value = 'internalEvents.asistenciaInvalida'
    return
  }

  if (!esEventoPasado(eventoAsistencia.value)) {
    errorOperacion.value = 'internalEvents.eventoPasado'
    return
  }

  procesando.value = true

  try {
    const respuesta = await solicitarGestion(
      `events/${eventoAsistencia.value.id}/attendance/`,
      "PATCH",
      { asistentes_reales: cantidad }
    )

    if (respuesta.status === 401) {
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      errorOperacion.value = 'internalEvents.sinPermiso'
      await cargarUsuario()
      return
    }

    if (!respuesta.ok) {
      errorOperacion.value = await obtenerMensajeError(respuesta)
      return
    }

    cerrarAsistencia()
    await cargarEventos()
    mensaje.value = 'internalEvents.asistenciaGuardada'
  } catch {
    errorOperacion.value = 'internalEvents.errorOperacion'
  } finally {
    procesando.value = false
  }
}

// SIAM-15: abre la edición cargando los datos reales.
async function iniciarEdicion(evento) {
  if (!puedeEditar.value || !esEventoFuturo(evento)) return

  limpiarOperacion()
  eventoCancelando.value = null
  cerrarAsistencia()
  procesando.value = true

  try {
    const respuesta = await solicitar(`events/${evento.id}/`)

    if (respuesta.status === 401) {
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      emit("sin-acceso")
      return
    }

    if (!respuesta.ok) {
      throw new Error('internalEvents.errorOperacion')
    }

    const datos = await respuesta.json()

    if (datos.estado !== "programado" || !esEventoFuturo(datos)) {
      throw new Error('internalEvents.errorOperacion')
    }

    formulario.value = {
      fecha: fechaParaInput(datos.fecha),
      descripcion: datos.descripcion,
      ubicacion: datos.ubicacion,
      tipo: datos.tipo,
      asistentes_esperados: datos.asistentes_esperados,
    }

    eventoEditando.value = datos

    await mostrarPanelGestion()
  } catch (error) {
    errorOperacion.value = error.message || 'internalEvents.errorOperacion'
  } finally {
    procesando.value = false
  }
}

// Procesa los errores que devuelve Django.
async function obtenerMensajeError(respuesta) {
  try {
    const datos = await respuesta.json()

    if (typeof datos.detail === "string") {
      return datos.detail
    }

    if (Array.isArray(datos)) {
      return datos[0] || 'internalEvents.errorOperacion'
    }

    const mensajes = Object.values(datos)
      .flat()
      .filter(valor => typeof valor === "string")

    return mensajes[0] || 'internalEvents.errorOperacion'
  } catch {
    return 'internalEvents.errorOperacion'
  }
}

// SIAM-15: guarda los cambios del evento.
async function guardarCambios() {
  if (!eventoEditando.value || procesando.value) return

  limpiarOperacion()

  const nuevaFecha = new Date(formulario.value.fecha)

  if (
    Number.isNaN(nuevaFecha.getTime()) ||
    nuevaFecha.getTime() <= Date.now()
  ) {
    errorOperacion.value = 'internalEvents.fechaInvalida'
    return
  }

  procesando.value = true

  try {
    const respuesta = await solicitarGestion(
      `events/${eventoEditando.value.id}/`,
      "PATCH",
      {
        fecha: nuevaFecha.toISOString(),
        descripcion: formulario.value.descripcion,
        ubicacion: formulario.value.ubicacion,
        tipo: formulario.value.tipo,
        asistentes_esperados: Number(
          formulario.value.asistentes_esperados
        ),
      }
    )

    if (respuesta.status === 401) {
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      errorOperacion.value = 'internalEvents.sinPermiso'
      await cargarUsuario()
      return
    }

    if (!respuesta.ok) {
      errorOperacion.value = await obtenerMensajeError(respuesta)
      return
    }

    cerrarEdicion()
    await cargarEventos()
    mensaje.value = 'internalEvents.modificado'
  } catch {
    errorOperacion.value = 'internalEvents.errorOperacion'
  } finally {
    procesando.value = false
  }
}

// SIAM-15: solicita confirmación antes de cancelar.
async function iniciarCancelacion(evento) {
  if (!puedeCancelar.value || !esEventoFuturo(evento)) return

  limpiarOperacion()
  cerrarEdicion()
  cerrarAsistencia()
  eventoCancelando.value = evento

  await mostrarPanelGestion()
}

// SIAM-15: cancela sin eliminar el registro.
async function confirmarCancelacion() {
  if (!eventoCancelando.value || procesando.value) return

  limpiarOperacion()
  procesando.value = true

  try {
    const respuesta = await solicitarGestion(
      `events/${eventoCancelando.value.id}/cancel/`,
      "POST",
      { confirm: true }
    )

    if (respuesta.status === 401) {
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      errorOperacion.value = 'internalEvents.sinPermiso'
      await cargarUsuario()
      return
    }

    if (!respuesta.ok) {
      errorOperacion.value = await obtenerMensajeError(respuesta)
      return
    }

    cerrarCancelacion()
    await cargarEventos()
    mensaje.value = 'internalEvents.cancelado'
  } catch {
    errorOperacion.value = 'internalEvents.errorOperacion'
  } finally {
    procesando.value = false
  }
}

onMounted(async () => {
  await cargarUsuario()
  await cargarEventos()
})
</script>

<template>
  <section class="eventos-internos">
    <header class="encabezado-eventos">
      <div>
        <h2>{{ t('internalEvents.titulo') }}</h2>
        <p>{{ t('internalEvents.descripcion') }}</p>
      </div>

      <button
        type="button"
        :disabled="cargando || procesando"
        @click="cargarEventos"
      >
        {{ t('internalEvents.actualizar') }}
      </button>
    </header>

    <p v-if="mensaje" role="status" class="mensaje-exito">
      {{ t(mensaje) }}
    </p>

    <p v-if="errorOperacion" role="alert" class="mensaje-error">
      {{ te(errorOperacion) ? t(errorOperacion) : errorOperacion }}
    </p>

    <!-- SIAM-15: formulario para modificar eventos -->
    <section
      v-if="eventoEditando"
      ref="panelGestion"
      class="panel-gestion"
      :aria-label="t('internalEvents.editarTitulo')"
    >
      <h3>{{ t('internalEvents.editarTitulo') }}</h3>

      <form class="formulario-evento" @submit.prevent="guardarCambios">
        <div class="campo">
          <label for="editar-fecha">{{ t('internalEvents.fecha') }}</label>
          <input
            id="editar-fecha"
            v-model="formulario.fecha"
            type="datetime-local"
            required
            :disabled="procesando"
          />
        </div>

        <div class="campo">
          <label for="editar-descripcion">
            {{ t('internalEvents.descripcionEvento') }}
          </label>
          <textarea
            id="editar-descripcion"
            v-model="formulario.descripcion"
            maxlength="500"
            rows="4"
            required
            :disabled="procesando"
          ></textarea>
        </div>

        <div class="campo">
          <label for="editar-ubicacion">{{ t('internalEvents.ubicacion') }}</label>
          <input
            id="editar-ubicacion"
            v-model="formulario.ubicacion"
            type="text"
            maxlength="200"
            required
            :disabled="procesando"
          />
        </div>

        <div class="campo">
          <label for="editar-tipo">{{ t('internalEvents.tipoEvento') }}</label>
          <select
            id="editar-tipo"
            v-model="formulario.tipo"
            :disabled="procesando"
          >
            <option value="publico">{{ t('internalEvents.publico') }}</option>
            <option value="privado">{{ t('internalEvents.privado') }}</option>
          </select>
        </div>

        <div class="campo">
          <label for="editar-asistentes">{{ t('internalEvents.asistentes') }}</label>
          <input
            id="editar-asistentes"
            v-model.number="formulario.asistentes_esperados"
            type="number"
            min="1"
            step="1"
            required
            :disabled="procesando"
          />
        </div>

        <div class="acciones-evento">
          <button type="submit" :disabled="procesando">
            {{ procesando ? t('internalEvents.guardando') : t('internalEvents.guardar') }}
          </button>

          <button
            type="button"
            class="boton-secundario"
            :disabled="procesando"
            @click="cerrarEdicion"
          >
            {{ t('internalEvents.descartar') }}
          </button>
        </div>
      </form>
    </section>

    <!-- SIAM-15: confirmación para cancelar eventos -->
    <section
      v-if="eventoCancelando"
      ref="panelGestion"
      class="panel-gestion"
      role="group"
      :aria-label="t('internalEvents.confirmarTitulo')"
    >
      <h3>{{ t('internalEvents.confirmarTitulo') }}</h3>

      <p>{{ t('internalEvents.confirmarMensaje') }}</p>
      <p><strong>{{ eventoCancelando.descripcion }}</strong></p>
      <p>{{ formatearFecha(eventoCancelando.fecha) }}</p>

      <div class="acciones-evento">
        <button
          type="button"
          class="boton-peligro"
          :disabled="procesando"
          @click="confirmarCancelacion"
        >
          {{ procesando ? t('internalEvents.guardando') : t('internalEvents.confirmar') }}
        </button>

        <button
          type="button"
          class="boton-secundario"
          :disabled="procesando"
          @click="cerrarCancelacion"
        >
          {{ t('internalEvents.volver') }}
        </button>
      </div>
    </section>

    <!-- SIAM-16: formulario de asistencia real -->
    <section
      v-if="eventoAsistencia"
      ref="panelGestion"
      class="panel-gestion"
      :aria-label="t('internalEvents.asistenciaTitulo')"
    >
      <h3>{{ t('internalEvents.asistenciaTitulo') }}</h3>

      <p>
        <strong>{{ eventoAsistencia.descripcion }}</strong>
      </p>

      <p>
        {{ formatearFecha(eventoAsistencia.fecha) }}
        ·
        {{ formatearHora(eventoAsistencia.fecha) }}
      </p>

      <form class="formulario-evento" @submit.prevent="guardarAsistencia">
        <div class="campo">
          <label for="asistencia-real">
            {{ t('internalEvents.asistentesReales') }}
          </label>

          <input
            id="asistencia-real"
            v-model="cantidadAsistencia"
            type="number"
            inputmode="numeric"
            min="0"
            max="2147483647"
            step="1"
            required
            :disabled="procesando"
          />
        </div>

        <div class="acciones-evento">
          <button type="submit" :disabled="procesando">
            {{ procesando ? t('internalEvents.guardando') : t('internalEvents.guardar') }}
          </button>

          <button
            type="button"
            class="boton-secundario"
            :disabled="procesando"
            @click="cerrarAsistencia"
          >
            {{ t('internalEvents.descartar') }}
          </button>
        </div>
      </form>
    </section>

    <p v-if="cargando" role="status">
      {{ t('internalEvents.cargando') }}
    </p>

    <p v-else-if="error" role="alert" class="mensaje-error">
      {{ t('internalEvents.error') }}
    </p>

    <template v-else>
      <!-- SIAM-14: calendario interno -->
      <section class="calendario" :aria-label="t('internalEvents.titulo')">
        <div class="navegacion-calendario">
          <h3 class="titulo-mes">{{ tituloMes }}</h3>

          <div class="controles-calendario">
            <button
              type="button"
              :aria-label="t('internalEvents.anterior')"
              @click="cambiarMes(-1)"
            >
              <span aria-hidden="true">‹</span>
            </button>

            <button type="button" @click="volverHoy">
              {{ t('internalEvents.hoy') }}
            </button>

            <button
              type="button"
              :aria-label="t('internalEvents.siguiente')"
              @click="cambiarMes(1)"
            >
              <span aria-hidden="true">›</span>
            </button>
          </div>
        </div>

        <div class="cuadricula-calendario">
          <div
            v-for="(nombre, indice) in encabezadosSemana"
            :key="`semana-${indice}`"
            class="nombre-dia"
          >
            {{ nombre }}
          </div>

          <template
            v-for="(fecha, indice) in diasCalendario"
            :key="`dia-${indice}`"
          >
            <div
              v-if="!fecha"
              class="dia-vacio"
              aria-hidden="true"
            ></div>

            <button
              v-else
              type="button"
              class="dia-calendario"
              :class="{
                seleccionado: mismoDia(fecha, diaSeleccionado),
                'con-eventos': eventosDelDia(fecha).length > 0,
                'es-hoy': mismoDia(fecha, new Date()),
              }"
              :aria-pressed="mismoDia(fecha, diaSeleccionado)"
              :aria-label="`${formatearFecha(fecha)}. ${eventosDelDia(fecha).length} ${t('internalEvents.cantidad')}`"
              @click="seleccionarDia(fecha)"
            >
              <span>{{ fecha.getDate() }}</span>

              <span
                v-if="eventosDelDia(fecha).length"
                class="indicadores-eventos"
                aria-hidden="true"
              >
                <span
                  v-if="eventosDelDia(fecha).some(
                    evento => evento.tipo === 'publico'
                  )"
                  class="indicador-eventos"
                ></span>

                <span
                  v-if="eventosDelDia(fecha).some(
                    evento => evento.tipo === 'privado'
                  )"
                  class="indicador-eventos indicador-privado"
                ></span>
              </span>
            </button>
          </template>
        </div>
      </section>

      <!-- Eventos del día seleccionado -->
      <section class="detalle-dia">
        <h3>{{ tituloDiaSeleccionado }}</h3>

        <p v-if="eventosSeleccionados.length === 0">
          {{ t('internalEvents.sinEventosDia') }}
        </p>

        <div v-else class="lista-eventos">
          <article
            v-for="evento in eventosSeleccionados"
            :key="evento.id"
            class="tarjeta-evento"
          >
            <div class="fecha-evento">
              <span>{{ formatearHora(evento.fecha) }}</span>

              <span
                class="etiqueta-tipo"
                :class="{ 'tipo-privado': evento.tipo === 'privado' }"
              >
                {{ nombreTipo(evento.tipo) }}
              </span>
            </div>

            <h4>{{ evento.descripcion }}</h4>

            <p>
              <strong>{{ t('internalEvents.ubicacion') }}:</strong>
              {{ evento.ubicacion }}
            </p>

            <!-- SIAM-16: mostrar asistencia en eventos pasados -->
            <p v-if="esEventoPasado(evento)">
              <strong>{{ t('internalEvents.asistentesReales') }}:</strong>
              {{
                tieneAsistencia(evento)
                  ? evento.asistentes_reales
                  : t('internalEvents.noRegistrada')
              }}
            </p>

            <!-- SIAM-16: registro o corrección de asistencia -->
            <div
              v-if="esEventoPasado(evento) && puedeRegistrarAsistencia"
              class="acciones-evento"
            >
              <button
                type="button"
                :disabled="procesando"
                @click="iniciarAsistencia(evento)"
              >
                {{
                  tieneAsistencia(evento)
                    ? t('internalEvents.corregirAsistencia')
                    : t('internalEvents.registrarAsistencia')
                }}
              </button>
            </div>

            <!-- SIAM-15: edición y cancelación futuras -->
            <div
              v-if="esEventoFuturo(evento) && (puedeEditar || puedeCancelar)"
              class="acciones-evento"
            >
              <button
                v-if="puedeEditar"
                type="button"
                :disabled="procesando"
                @click="iniciarEdicion(evento)"
              >
                {{ t('internalEvents.editar') }}
              </button>

              <button
                v-if="puedeCancelar"
                type="button"
                class="boton-peligro"
                :disabled="procesando"
                @click="iniciarCancelacion(evento)"
              >
                {{ t('internalEvents.cancelar') }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <!-- Próximos eventos públicos y privados -->
      <section class="proximos-eventos">
        <h3>{{ t('internalEvents.proximos') }}</h3>

        <p v-if="proximosEventos.length === 0" role="status">
          {{ t('internalEvents.sinProximos') }}
        </p>

        <div v-else class="lista-eventos">
          <article
            v-for="evento in proximosEventos"
            :key="evento.id"
            class="tarjeta-evento"
          >
            <div class="fecha-evento">
              <span>{{ formatearFecha(evento.fecha) }}</span>
              <span>{{ formatearHora(evento.fecha) }}</span>

              <span
                class="etiqueta-tipo"
                :class="{ 'tipo-privado': evento.tipo === 'privado' }"
              >
                {{ nombreTipo(evento.tipo) }}
              </span>
            </div>

            <h4>{{ evento.descripcion }}</h4>

            <p>
              <strong>{{ t('internalEvents.ubicacion') }}:</strong>
              {{ evento.ubicacion }}
            </p>

            <div
              v-if="puedeEditar || puedeCancelar"
              class="acciones-evento"
            >
              <button
                v-if="puedeEditar"
                type="button"
                :disabled="procesando"
                @click="iniciarEdicion(evento)"
              >
                {{ t('internalEvents.editar') }}
              </button>

              <button
                v-if="puedeCancelar"
                type="button"
                class="boton-peligro"
                :disabled="procesando"
                @click="iniciarCancelacion(evento)"
              >
                {{ t('internalEvents.cancelar') }}
              </button>
            </div>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.eventos-internos {
  width: 100%;
  max-width: 1000px;
  min-width: 0;
  margin: 0 auto;
  color: var(--color-texto);
}

.encabezado-eventos {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 28px;
}

.encabezado-eventos h2 {
  margin-top: 0;
  color: var(--color-enlace);
}

.encabezado-eventos p {
  line-height: 1.6;
}

button {
  box-sizing: border-box;
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

.calendario,
.panel-gestion {
  padding: 20px;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-control);
}

.panel-gestion {
  margin-bottom: 28px;
  scroll-margin-top: 20px;
}

.panel-gestion h3 {
  margin-top: 0;
  color: var(--color-enlace);
}

.navegacion-calendario {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
}

.titulo-mes {
  margin: 0;
}

.controles-calendario {
  display: flex;
  align-items: center;
  gap: 8px;
}

.controles-calendario button {
  min-width: 44px;
}

.cuadricula-calendario {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 5px;
}

.nombre-dia {
  padding: 8px 0;
  text-align: center;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: capitalize;
}

.dia-vacio {
  min-height: 60px;
}

.dia-calendario {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-width: 0;
  min-height: 60px;
  padding: 5px;
  background: var(--color-control);
  color: var(--color-texto);
  border: 1px solid var(--color-borde);
  border-radius: 6px;
}

.dia-calendario.seleccionado {
  background: var(--color-header);
  color: #ffffff;
  border-color: var(--color-header);
}

.dia-calendario.es-hoy {
  outline: 2px solid var(--color-enlace);
  outline-offset: -3px;
}

.indicadores-eventos {
  display: flex;
  gap: 4px;
}

.indicador-eventos {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-enlace);
}

.indicador-privado {
  background: #e49a37;
}

.seleccionado .indicador-eventos:not(.indicador-privado) {
  background: #ffffff;
}

.detalle-dia,
.proximos-eventos {
  margin-top: 32px;
}

.lista-eventos {
  display: grid;
  gap: 18px;
}

.tarjeta-evento {
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-control);
  overflow-wrap: anywhere;
}

.fecha-evento {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
  font-weight: 600;
  color: var(--color-enlace);
}

.etiqueta-tipo {
  display: inline-block;
  padding: 4px 10px;
  border: 1px solid var(--color-borde);
  border-radius: 20px;
  background: var(--color-control);
  color: var(--color-texto);
  font-size: 0.85rem;
}

.tipo-privado {
  border-color: #d59539;
  color: var(--color-texto);
}

.tarjeta-evento h4 {
  margin: 16px 0;
  font-size: 1.15rem;
}

.tarjeta-evento p {
  margin-bottom: 0;
  line-height: 1.6;
}

.acciones-evento {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.boton-secundario {
  background: var(--color-control);
  color: var(--color-texto);
}

.boton-peligro {
  background: #a82018;
  border-color: #a82018;
  color: #ffffff;
}

.formulario-evento {
  display: grid;
  gap: 16px;
}

.campo {
  display: grid;
  gap: 8px;
}

.campo label {
  font-weight: 600;
}

.campo input,
.campo textarea,
.campo select {
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

.campo textarea {
  resize: vertical;
}

.mensaje-error {
  color: var(--color-error);
}

.mensaje-exito {
  color: var(--color-enlace);
  font-weight: 600;
}

@media (max-width: 767px) {
  .encabezado-eventos {
    flex-direction: column;
  }

  .encabezado-eventos > button {
    width: 100%;
  }

  .calendario,
  .panel-gestion {
    padding: 10px;
  }

  .dia-calendario,
  .dia-vacio {
    min-height: 48px;
  }

  .nombre-dia {
    font-size: 0.75rem;
  }

  .tarjeta-evento {
    padding: 16px;
  }
}

@media (max-width: 400px) {
  .cuadricula-calendario {
    gap: 3px;
  }

  .dia-calendario {
    padding: 3px;
  }

  .controles-calendario {
    width: 100%;
    justify-content: space-between;
  }

  .acciones-evento button {
    width: 100%;
  }
}
</style>
