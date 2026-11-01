
<script setup>
import { computed, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import { formatearFecha, formatearHora } from "../i18n/index.js"

const { t, locale } = useI18n({ useScope: "global" })

const eventos = ref([])
const cargando = ref(false)
const error = ref(false)

// SIAM-9: mes visible y día seleccionado.
const hoy = new Date()
const mesActual = ref(new Date(hoy.getFullYear(), hoy.getMonth(), 1))
const diaSeleccionado = ref(new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate()))

const idiomaRegional = computed(() =>
  locale.value === "en" ? "en-US" : "es-CR"
)

const tituloMes = computed(() => {
  const titulo = new Intl.DateTimeFormat(idiomaRegional.value, {
    month: "long",
    year: "numeric",
  }).format(mesActual.value)

  return titulo.charAt(0).toUpperCase() + titulo.slice(1)
})

const encabezadosSemana = computed(() => {
  const lunes = new Date(2024, 0, 1)

  return Array.from({ length: 7 }, (_, indice) => {
    const fecha = new Date(2024, 0, 1 + indice)

    return new Intl.DateTimeFormat(idiomaRegional.value, {
      weekday: "short",
    }).format(fecha)
  })
})

// Compara días utilizando la fecha local del navegador.
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

// Genera las casillas del calendario comenzando por lunes.
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

const tituloDiaSeleccionado = computed(() =>
  formatearFecha(diaSeleccionado.value)
)

function cambiarMes(cantidad) {
  const anio = mesActual.value.getFullYear()
  const mes = mesActual.value.getMonth()

  mesActual.value = new Date(anio, mes + cantidad, 1)

  // Al cambiar de mes, seleccionamos su primer día.
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

// Conservamos la consulta pública implementada en SIAM-13.
async function cargarEventos() {
  cargando.value = true
  error.value = false

  try {
    const respuesta = await solicitar("events/")

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
          evento.tipo === "publico" &&
          Number.isFinite(fecha) &&
          fecha >= Date.now()
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

onMounted(cargarEventos)
</script>

<template>
  <section class="eventos-publicos">
    <header class="encabezado-eventos">
      <div>
        <h1>{{ t("publicEvents.title") }}</h1>
        <p>{{ t("publicEvents.description") }}</p>
      </div>

      <button
        type="button"
        :disabled="cargando"
        @click="cargarEventos"
      >
        {{ t("publicEvents.refresh") }}
      </button>
    </header>

    <p v-if="cargando" role="status">
      {{ t("publicEvents.loading") }}
    </p>

    <p v-else-if="error" role="alert" class="mensaje-error">
      {{ t("publicEvents.loadError") }}
    </p>

    <template v-else>
      <!-- SIAM-9: Calendario mensual de eventos públicos. -->
      <section class="calendario" :aria-label="t('publicEvents.calendar')">
        <div class="navegacion-calendario">
          <h2 class="titulo-mes">{{ tituloMes }}</h2>

          <div class="controles-calendario">
            <button
              type="button"
              :aria-label="t('publicEvents.previousMonth')"
              @click="cambiarMes(-1)"
            >
              <span aria-hidden="true">‹</span>
            </button>

            <button type="button" @click="volverHoy">
              {{ t("publicEvents.today") }}
            </button>

            <button
              type="button"
              :aria-label="t('publicEvents.nextMonth')"
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
            <div v-if="!fecha" class="dia-vacio" aria-hidden="true"></div>

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
              :aria-label="`${formatearFecha(fecha)}. ${eventosDelDia(fecha).length} ${t('publicEvents.eventCount')}`"
              @click="seleccionarDia(fecha)"
            >
              <span>{{ fecha.getDate() }}</span>
              <span
                v-if="eventosDelDia(fecha).length"
                class="indicador-eventos"
                aria-hidden="true"
              ></span>
            </button>
          </template>
        </div>
      </section>

      <!-- Eventos correspondientes al día elegido. -->
      <section class="detalle-dia">
        <h2>{{ tituloDiaSeleccionado }}</h2>

        <p v-if="eventosSeleccionados.length === 0">
          {{ t("publicEvents.noEventsOnDay") }}
        </p>

        <div v-else class="lista-eventos">
          <article
            v-for="evento in eventosSeleccionados"
            :key="evento.id"
            class="tarjeta-evento"
          >
            <div class="fecha-evento">
              <span>{{ formatearHora(evento.fecha) }}</span>
            </div>

            <h3>{{ evento.descripcion }}</h3>

            <p>
              <strong>{{ t("publicEvents.location") }}:</strong>
              {{ evento.ubicacion }}
            </p>
          </article>
        </div>
      </section>

      <!-- Conservamos la lista de SIAM-13. -->
      <section class="proximos-eventos">
        <h2>{{ t("publicEvents.upcoming") }}</h2>

        <p v-if="eventos.length === 0" role="status">
          {{ t("publicEvents.empty") }}
        </p>

        <div v-else class="lista-eventos">
          <article
            v-for="evento in eventos"
            :key="evento.id"
            class="tarjeta-evento"
          >
            <div class="fecha-evento">
              <span>{{ formatearFecha(evento.fecha) }}</span>
              <span>{{ formatearHora(evento.fecha) }}</span>
            </div>

            <h3>{{ evento.descripcion }}</h3>

            <p>
              <strong>{{ t("publicEvents.location") }}:</strong>
              {{ evento.ubicacion }}
            </p>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.eventos-publicos {
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

.encabezado-eventos h1 {
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

/* Calendario público */
.calendario {
  padding: 20px;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-control);
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

.indicador-eventos {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-enlace);
}

.seleccionado .indicador-eventos {
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
  gap: 8px 16px;
  font-weight: 600;
  color: var(--color-enlace);
}

.tarjeta-evento h3 {
  margin: 16px 0;
  font-size: 1.15rem;
}

.tarjeta-evento p {
  margin-bottom: 0;
  line-height: 1.6;
}

.mensaje-error {
  color: var(--color-error);
}

@media (max-width: 767px) {
  .encabezado-eventos {
    flex-direction: column;
  }

  .encabezado-eventos > button {
    width: 100%;
  }

  .calendario {
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
}
</style>
