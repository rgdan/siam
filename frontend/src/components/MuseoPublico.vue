
<script setup>
import { computed, onMounted, reactive, ref } from "vue"
import { useI18n } from "vue-i18n"
import { museoProvisional } from "../data/museo.js"

const museo = reactive(structuredClone(museoProvisional))
const errorConfiguracion = ref(false)
const cargando = ref(true)

onMounted(async () => {
  try {
    const base = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/"
    const response = await fetch(`${base}public/configuration/`, { cache: "no-store", signal: AbortSignal.timeout(5000) })
    if (!response.ok) throw new Error("configuration")
    const config = await response.json()
    museo.nombre = config.museum_name
    museo.localidad = config.location
    // La dirección de referencia ya tiene sus textos en español e inglés.
    if (config.address !== museoProvisional.ubicacion.es) {
      const ubicacion = `${config.address} ${config.location}`
      museo.ubicacion = { es: ubicacion, en: ubicacion }
    }
    museo.horarios = Object.entries(config.opening_hours)
      .map(([dia, hours]) => ({ dia: Number(dia), apertura: hours.opens, cierre: hours.closes }))
      .sort((a, b) => ((a.dia + 6) % 7) - ((b.dia + 6) % 7))
    let preferred = null
    try { preferred = localStorage.getItem("siam-idioma") } catch {  }
    if (preferred !== "es" && preferred !== "en") {
      locale.value = config.default_language
      document.documentElement.lang = config.default_language
    }
  } catch {
    errorConfiguracion.value = true
  } finally {
    cargando.value = false
  }
})

const { t, locale } = useI18n({ useScope: "global" })

const dias = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
]

const historia = computed(() =>
  museo.historia[locale.value] ??
  museo.historia.es
)

const ubicacion = computed(() =>
  museo.ubicacion[locale.value] ??
  museo.ubicacion.es
)

function formatearHorario(hora) {
  if (!hora) return ""

  const [horas, minutos] = hora.split(":").map(Number)

  const fecha = new Date(2026, 0, 1, horas, minutos)

  return new Intl.DateTimeFormat(
    locale.value === "en" ? "en-US" : "es-CR",
    {
      hour: "numeric",
      minute: "2-digit",
    }
  ).format(fecha)
}

const horarios = computed(() =>
  museo.horarios.map((horario) => ({
    ...horario,
    nombre: t(`museum.days.${dias[horario.dia]}`),
    cerrado: !horario.apertura || !horario.cierre,
    aperturaFormateada: formatearHorario(horario.apertura),
    cierreFormateado: formatearHorario(horario.cierre),
  }))
)

// El resumen se calcula con los horarios actuales, no con cifras del prototipo.
const diasAbiertos = computed(() => horarios.value.filter(horario => !horario.cerrado).length)
</script>

<template>
  <div class="museo-publico">
    <header class="encabezado-museo">
      <h1>{{ museo.nombre }}</h1>
      <p>{{ t("common.systemName") }} · SIAM</p>
    </header>

    <p v-if="cargando" role="status">{{ t("common.processing") }}</p>
    <p v-if="errorConfiguracion" role="alert">{{ locale === "en" ? "Current information could not be loaded. Showing reference information." : "No se pudo cargar la información actual. Se muestran datos de referencia." }}</p>

    <dl class="resumen-museo">
      <div class="tarjeta-resumen">
        <dt>{{ t("museum.openDays") }}</dt>
        <dd>{{ diasAbiertos }}</dd>
      </div>
      <div class="tarjeta-resumen">
        <dt>{{ t("museum.admission") }}</dt>
        <dd>{{ t(museo.entradaGratuita ? "museum.free" : "museum.askAdmission") }}</dd>
      </div>
      <div class="tarjeta-resumen">
        <dt>{{ t("museum.location") }}</dt>
        <dd class="localidad">{{ museo.localidad }}</dd>
      </div>
    </dl>

    <section class="seccion-museo" aria-labelledby="titulo-horarios">
      <h2 id="titulo-horarios">{{ t("museum.hours") }}</h2>
      <p v-if="!horarios.length">{{ t("museum.noHours") }}</p>
      <dl v-else class="horarios">
        <div v-for="horario in horarios" :key="horario.dia" class="horario">
          <dt>{{ horario.nombre }}</dt>
          <dd>{{ horario.cerrado ? t("museum.closed") : `${horario.aperturaFormateada} - ${horario.cierreFormateado}` }}</dd>
        </div>
      </dl>
    </section>

    <section class="seccion-museo" aria-labelledby="titulo-historia">
      <h2 id="titulo-historia">{{ t("museum.history") }}</h2>
      <p>{{ historia }}</p>
      <h3>{{ t("museum.location") }}</h3>
      <p>{{ ubicacion }}</p>
    </section>
  </div>
</template>

<style scoped>
.museo-publico {
  width: 100%;
  max-width: 704px;
  min-width: 0;
  color: var(--color-texto);
}

.encabezado-museo { margin-bottom: 32px; }
.encabezado-museo h1 { margin: 0; font-size: clamp(26px, 2vw, 32px); line-height: 1.2; }
.encabezado-museo p { margin: 10px 0 0; color: var(--color-secundario); font-size: 13px; }
.resumen-museo { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin: 0 0 32px; }
.tarjeta-resumen { display: flex; flex-direction: column; justify-content: center; gap: 8px; min-height: 124px; padding: 20px; border: 1px solid var(--color-divisor); border-radius: 14px; background: var(--color-superficie); box-shadow: 0 1px 2px #00000018; }
.tarjeta-resumen dt { order: 2; color: var(--color-secundario); font-size: 12px; }
.tarjeta-resumen dd { order: 1; margin: 0; color: var(--color-enlace); font-size: 26px; font-variant-numeric: tabular-nums; }
.tarjeta-resumen .localidad { font-size: 20px; }

.seccion-museo {
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid var(--color-divisor);
  border-radius: 16px;
  background: var(--color-superficie);
  box-shadow: 0 1px 2px #00000018;
}

.seccion-museo h2,
.seccion-museo h3 {
  color: var(--color-enlace);
  margin-top: 0;
}
.seccion-museo h2 { font-size: 21px; }
.seccion-museo h3 { font-size: 17px; margin-top: 24px; }

.seccion-museo p {
  line-height: 1.6;
}

.seccion-museo p { font-size: 14px; }
.horarios { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 16px; margin: 0; }
.horario { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; min-height: 44px; padding-block: 12px; border-bottom: 1px solid var(--color-divisor); font-size: 12px; }
.horario dt { color: var(--color-secundario); }
.horario dd { margin: 0; }
.museo-publico { overflow-wrap: anywhere; }
@media (min-width: 801px) and (max-width: 1040px) {
  .resumen-museo { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .resumen-museo, .horarios { grid-template-columns: minmax(0, 1fr); }
  .tarjeta-resumen { min-height: 100px; }
  .seccion-museo {
    padding: 16px;
  }
}
</style>
