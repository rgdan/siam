<script setup>
import { nextTick, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import RegistrarIncidencia from "./RegistrarIncidencia.vue"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t, locale } = useI18n({ useScope: "global" })
const incidencias = ref([])
const cargando = ref(true)
const error = ref(false)
const mostrarFormulario = ref(false)
const registrada = ref(false)
const botonRegistro = ref(null)
const titulo = ref(null)
const pagina = ref(1)
const total = ref(0)
const anterior = ref(false)
const siguiente = ref(false)
const orden = ref("-timestamp")

async function cargar(numero = pagina.value) {
  const restaurarFoco = numero !== pagina.value || error.value
  pagina.value = numero
  cargando.value = true
  error.value = false
  try {
    const parametros = new URLSearchParams({ page: String(numero), ordering: orden.value })
    const respuesta = await solicitar(`incidents/?${parametros}`)
    if (respuesta.status === 401 || respuesta.status === 403) {
      incidencias.value = []
      emit(respuesta.status === 401 ? "sesion-expirada" : "sin-acceso")
      return
    }
    if (!respuesta.ok) throw new Error()
    const datos = await respuesta.json()
    incidencias.value = datos.results
    total.value = datos.count
    anterior.value = Boolean(datos.previous)
    siguiente.value = Boolean(datos.next)
  } catch {
    error.value = true
  } finally {
    cargando.value = false
  }
  if (restaurarFoco && !error.value) {
    await nextTick()
    titulo.value?.focus()
  }
}

async function volver() {
  mostrarFormulario.value = false
  await nextTick()
  botonRegistro.value?.focus()
}

async function alGuardar() {
  registrada.value = true
  mostrarFormulario.value = false
  await cargar(1)
  await nextTick()
  botonRegistro.value?.focus()
}

function fecha(valor, opciones) {
  return new Intl.DateTimeFormat(locale.value === "en" ? "en-US" : "es-CR", opciones).format(new Date(valor))
}

onMounted(cargar)
</script>

<template>
  <RegistrarIncidencia
    v-if="mostrarFormulario"
    @guardada="alGuardar"
    @cancelar="volver"
    @sesion-expirada="emit('sesion-expirada')"
    @sin-acceso="emit('sin-acceso')"
  />

  <section v-else class="historial-incidencias" aria-labelledby="titulo-incidencias">
    <header class="encabezado">
      <div>
        <h1 id="titulo-incidencias" ref="titulo" tabindex="-1">{{ t("incidents.listTitle") }}</h1>
        <p v-if="!cargando && !error">{{ t("incidents.count", { count: total }) }}</p>
      </div>
      <button ref="botonRegistro" type="button" class="reportar" :disabled="cargando" @click="registrada = false; mostrarFormulario = true">
        <span aria-hidden="true">+</span> {{ t("incidents.report") }}
      </button>
    </header>

    <div class="orden">
      <label for="orden-incidencias">{{ t("incidents.sortByDate") }}</label>
      <select id="orden-incidencias" v-model="orden" :disabled="cargando" @change="cargar(1)">
        <option value="-timestamp">{{ t("incidents.newestFirst") }}</option>
        <option value="timestamp">{{ t("incidents.oldestFirst") }}</option>
      </select>
    </div>

    <p v-if="registrada" role="status">{{ t("incidents.saved") }}</p>
    <p v-if="cargando" role="status">{{ t("incidents.loading") }}</p>
    <div v-else-if="error" role="alert">
      <p>{{ t("incidents.loadError") }}</p>
      <button type="button" @click="cargar()">{{ t("incidents.reload") }}</button>
    </div>
    <p v-else-if="incidencias.length === 0">{{ t("incidents.empty") }}</p>

    <ul v-else class="lista">
      <li v-for="incidencia in incidencias" :key="incidencia.id">
        <article class="incidencia">
          <time :datetime="incidencia.timestamp" class="fecha">
            <span>{{ fecha(incidencia.timestamp, { dateStyle: 'short' }) }}</span>
            <strong>{{ fecha(incidencia.timestamp, { hour: '2-digit', minute: '2-digit', hour12: false }) }}</strong>
          </time>
          <div class="detalle">
            <h2>{{ t(`incidents.categories.${incidencia.category}`) }}</h2>
            <p class="referencia">INC-{{ incidencia.id }} · {{ incidencia.user_name }}</p>
            <p class="descripcion">{{ incidencia.description }}</p>
          </div>
        </article>
      </li>
    </ul>

    <nav v-if="total > 0" class="paginacion" :aria-label="t('incidents.pagination')">
      <button type="button" :disabled="cargando || error || !anterior" @click="cargar(pagina - 1)">{{ t("incidents.previous") }}</button>
      <span role="status">{{ t("incidents.page", { page: pagina }) }}</span>
      <button type="button" :disabled="cargando || error || !siguiente" @click="cargar(pagina + 1)">{{ t("incidents.next") }}</button>
    </nav>
  </section>
</template>

<style scoped>
.historial-incidencias { overflow-wrap: anywhere; }
.encabezado { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 24px; }
h1 { margin: 0; }
.encabezado p { margin: 8px 0 0; color: var(--color-secundario); }
button { min-height: 44px; padding: 10px 18px; border: 1px solid var(--color-borde); border-radius: 7px; font: inherit; background: var(--color-control); color: var(--color-texto); cursor: pointer; }
.reportar { background: var(--color-acento); color: #fff; border-color: var(--color-acento); font-weight: 600; }
.reportar span { margin-right: 8px; }
button:enabled:hover, button:enabled:active { filter: brightness(0.9); }
button:disabled { cursor: wait; opacity: 0.6; }
.orden { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 20px; }
select { min-height: 44px; max-width: 100%; padding: 10px 12px; border: 1px solid var(--color-borde); border-radius: 7px; background: var(--color-control); color: var(--color-texto); font: inherit; }
.paginacion { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-top: 20px; }
.lista { display: grid; gap: 14px; padding: 0; margin: 0; list-style: none; }
.incidencia { display: flex; align-items: flex-start; gap: 16px; padding: 20px; border: 1px solid var(--color-divisor); border-radius: 12px; background: var(--color-superficie); }
.fecha { display: grid; gap: 4px; flex: 0 0 82px; padding: 10px 6px; border-radius: 7px; text-align: center; background: var(--color-header); color: #fff; font-size: 12px; }
.fecha strong { font-size: 16px; font-variant-numeric: tabular-nums; }
.detalle { min-width: 0; flex: 1; }
h2 { margin: 2px 0 6px; font: 600 16px system-ui, sans-serif; }
.referencia { margin: 0 0 10px; font-size: 13px; color: var(--color-secundario); }
.descripcion { margin: 0; line-height: 1.6; white-space: pre-wrap; }
@media (max-width: 480px) {
  .reportar { width: 100%; }
  .incidencia { padding: 16px 12px; gap: 12px; }
  .fecha { flex-basis: 72px; font-size: 11px; }
}
</style>
