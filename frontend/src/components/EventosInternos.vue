
<script setup>
import { computed, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import { formatearFecha, formatearHora } from "../i18n/index.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])

const { locale } = useI18n({ useScope: "global" })

const textos = {
  es: {
    titulo: "Calendario interno de eventos",
    descripcion: "Consulte los eventos públicos y privados del museo.",
    actualizar: "Actualizar eventos",
    cargando: "Cargando eventos...",
    error: "No se pudieron cargar los eventos.",
    anterior: "Mes anterior",
    siguiente: "Mes siguiente",
    hoy: "Hoy",
    cantidad: "eventos",
    sinEventosDia: "No hay eventos programados para este día.",
    proximos: "Próximos eventos",
    sinProximos: "No hay próximos eventos programados.",
    ubicacion: "Ubicación",
    publico: "Público",
    privado: "Privado",
  },
  en: {
    titulo: "Internal event calendar",
    descripcion: "View the museum's public and private events.",
    actualizar: "Refresh events",
    cargando: "Loading events...",
    error: "Events could not be loaded.",
    anterior: "Previous month",
    siguiente: "Next month",
    hoy: "Today",
    cantidad: "events",
    sinEventosDia: "There are no scheduled events for this day.",
    proximos: "Upcoming events",
    sinProximos: "There are no upcoming scheduled events.",
    ubicacion: "Location",
    publico: "Public",
    privado: "Private",
  },
}

const texto = computed(() =>
  textos[locale.value === "en" ? "en" : "es"]
)

const idiomaRegional = computed(() =>
  locale.value === "en" ? "en-US" : "es-CR"
)

const eventos = ref([])
const cargando = ref(false)
const error = ref(false)

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

// Genera el calendario comenzando por lunes.
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
    new Date(evento.fecha).getTime() >= Date.now()
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
    ? texto.value.privado
    : texto.value.publico
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
      throw new Error("No se pudieron consultar los eventos internos.")
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

onMounted(cargarEventos)
</script>

<template>
  <section class="eventos-internos">
    <header class="encabezado-eventos">
      <div>
        <h2>{{ texto.titulo }}</h2>
        <p>{{ texto.descripcion }}</p>
      </div>

      <button
        type="button"
        :disabled="cargando"
        @click="cargarEventos"
      >
        {{ texto.actualizar }}
      </button>
    </header>

    <p v-if="cargando" role="status">
      {{ texto.cargando }}
    </p>

    <p v-else-if="error" role="alert" class="mensaje-error">
      {{ texto.error }}
    </p>

    <template v-else>
      <!-- SIAM-14: calendario de eventos internos. -->
      <section class="calendario" :aria-label="texto.titulo">
        <div class="navegacion-calendario">
          <h3 class="titulo-mes">{{ tituloMes }}</h3>

          <div class="controles-calendario">
            <button
              type="button"
              :aria-label="texto.anterior"
              @click="cambiarMes(-1)"
            >
              <span aria-hidden="true">‹</span>
            </button>

            <button type="button" @click="volverHoy">
              {{ texto.hoy }}
            </button>

            <button
              type="button"
              :aria-label="texto.siguiente"
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
                'con-privados': eventosDelDia(fecha).some(
                  evento => evento.tipo === 'privado'
                ),
              }"
              :aria-pressed="mismoDia(fecha, diaSeleccionado)"
              :aria-label="`${formatearFecha(fecha)}. ${eventosDelDia(fecha).length} ${texto.cantidad}`"
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

      <!-- Eventos del día seleccionado. -->
      <section class="detalle-dia">
        <h3>{{ tituloDiaSeleccionado }}</h3>

        <p v-if="eventosSeleccionados.length === 0">
          {{ texto.sinEventosDia }}
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
              <strong>{{ texto.ubicacion }}:</strong>
              {{ evento.ubicacion }}
            </p>
          </article>
        </div>
      </section>

      <!-- Próximos eventos públicos y privados. -->
      <section class="proximos-eventos">
        <h3>{{ texto.proximos }}</h3>

        <p v-if="proximosEventos.length === 0" role="status">
          {{ texto.sinProximos }}
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
              <strong>{{ texto.ubicacion }}:</strong>
              {{ evento.ubicacion }}
            </p>
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
