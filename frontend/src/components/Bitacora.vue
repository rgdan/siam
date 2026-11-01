<script setup>
import { onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import { formatearFecha, formatearHora } from "../i18n/index.js"
import collectionMessages from "./collectionMessages.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t, te, locale } = useI18n({ useScope: "global" })
const registros = ref([])
const pagina = ref(1)
const total = ref(0)
const anterior = ref(false)
const siguiente = ref(false)
const cargando = ref(true)
const error = ref("")
const acciones = ["create", "modify", "decommission", "sensitive_read", "login", "failed_login"]
const entidades = ["piece", "user", "visitor_entry", "incident", "system_parameter", "access"]
const filtros = ref({ user: "", action_type: "", entity: "", date_from: "", date_to: "" })
let filtrosAplicados = {}

function nombreEntidad(registro) {
  return entidades.includes(registro.entity) ? t(`audit.entities.${registro.entity}`) : registro.entity
}

function nombreCampo(campo, entidad) {
  if (entidad === "piece") {
    const key = campo === "title" ? "pieceTitle" : campo === "photos" ? "photosField" : campo
    const label = collectionMessages[locale.value]?.[key]
    if (label) return label
  }
  return te(`audit.fields.${campo}`) ? t(`audit.fields.${campo}`) : campo.replaceAll("_", " ")
}

function valor(value, campo) {
  if (value === null || value === undefined || value === "") return t("audit.noValue")
  if (typeof value === "boolean") return t(value ? "audit.yes" : "audit.no")
  if (Array.isArray(value)) {
    if (!value.length) return t("audit.noValue")
    return value.map(item => campo === "photos" ? t("audit.photoReference", { id: item }) : valor(item, campo)).join(", ")
  }
  if (typeof value === "object")
    return Object.entries(value).map(([key, item]) => `${nombreCampo(key)}: ${valor(item, key)}`).join("; ")
  if (campo === "role" && te(`roles.${value}`)) return t(`roles.${value}`)
  if (["timestamp", "last_login"].includes(campo)) return `${formatearFecha(value)} ${formatearHora(value)}`
  if (campo === "state" && ["stored", "displayed"].includes(value)) return collectionMessages[locale.value][value]
  if (te(`audit.values.${campo}.${value}`)) return t(`audit.values.${campo}.${value}`)
  return String(value)
}

function tituloRegistro(registro) {
  const referencia = `${nombreEntidad(registro)}${registro.entity_id ? ` #${registro.entity_id}` : ""}`
  const cambios = registro.changes
  const nombre = cambios.title || cambios.full_name || cambios.email
  const identidad = nombre?.new || nombre?.old
  return `${t(`audit.actions.${registro.action_type}`)} · ${referencia}${identidad ? `: ${identidad}` : ""}`
}

function resumen(registro) {
  const campos = Object.keys(registro.changes).map(campo => nombreCampo(campo, registro.entity))
  if (!campos.length) return ""
  const fotoEliminada = registro.changes.photo
  if (fotoEliminada?.old && fotoEliminada.new === null)
    return t("audit.photoDeleted", { name: fotoEliminada.old.name })
  const fotos = registro.changes.photos
  if (campos.length === 1 && fotos && Array.isArray(fotos.old) && Array.isArray(fotos.new)) {
    const added = fotos.new.filter(id => !fotos.old.includes(id)).length
    const removed = fotos.old.filter(id => !fotos.new.includes(id)).length
    return [
      added ? t("audit.photosAdded", { count: added }) : "",
      removed ? t("audit.photosRemoved", { count: removed }) : "",
    ].filter(Boolean).join(" ")
  }
  if (registro.action_type === "create") return t("audit.createdFields", { count: campos.length })
  return t("audit.changedFields", { fields: campos.join(", ") })
}

// Conserva los filtros enviados aunque se edite el formulario mientras se navega entre páginas.
function aplicarFiltros() {
  filtrosAplicados = { ...filtros.value }
  cargar(1)
}

// Limpia los filtros y vuelve a consultar la primera página.
function limpiarFiltros() {
  filtros.value = { user: "", action_type: "", entity: "", date_from: "", date_to: "" }
  aplicarFiltros()
}

// Consulta páginas del endpoint existente; nunca sigue direcciones externas ni modifica registros.
async function cargar(numero = 1) {
  cargando.value = true
  error.value = ""
  registros.value = []
  pagina.value = numero
  try {
    const parametros = new URLSearchParams({ page: numero })
    for (const [nombre, valor] of Object.entries(filtrosAplicados)) {
      if (valor) parametros.set(nombre, valor)
    }
    const respuesta = await solicitar(`audit/?${parametros}`)
    if (respuesta.status === 401) {
      emit("sesion-expirada")
      return
    }
    if (respuesta.status === 403) {
      emit("sin-acceso")
      return
    }
    if (respuesta.status === 400) {
      error.value = "audit.invalidFilters"
      return
    }
    if (!respuesta.ok) throw new Error()
    const datos = await respuesta.json()
    if (!Array.isArray(datos.results)) throw new Error()
    registros.value = datos.results
    total.value = datos.count
    anterior.value = Boolean(datos.previous)
    siguiente.value = Boolean(datos.next)
  } catch {
    error.value = "audit.error"
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <section class="bitacora" aria-labelledby="titulo-bitacora" :aria-busy="cargando">
    <header class="cabecera">
      <h2 id="titulo-bitacora">{{ t("audit.title") }}</h2>
      <button type="button" :disabled="cargando" @click="cargar(pagina)">{{ t("audit.refresh") }}</button>
    </header>
    <form class="filtros" @submit.prevent="aplicarFiltros">
      <fieldset :disabled="cargando">
        <legend>{{ t("audit.filters") }}</legend>
        <div class="campos-filtro">
          <div>
            <label for="filtro-usuario">{{ t("audit.userFilter") }}</label>
            <input id="filtro-usuario" v-model.trim="filtros.user" type="email" maxlength="254" />
          </div>
          <div>
            <label for="filtro-accion">{{ t("audit.actionType") }}</label>
            <select id="filtro-accion" v-model="filtros.action_type">
              <option value="">{{ t("audit.allActions") }}</option>
              <option v-for="accion in acciones" :key="accion" :value="accion">{{ t(`audit.actions.${accion}`) }}</option>
            </select>
          </div>
          <div>
            <label for="filtro-entidad">{{ t("audit.entity") }}</label>
            <select id="filtro-entidad" v-model="filtros.entity">
              <option value="">{{ t("audit.allEntities") }}</option>
              <option v-for="entidad in entidades" :key="entidad" :value="entidad">{{ t(`audit.entities.${entidad}`) }}</option>
            </select>
          </div>
          <div>
            <label for="filtro-desde">{{ t("audit.dateFrom") }}</label>
            <input id="filtro-desde" v-model="filtros.date_from" type="date" :max="filtros.date_to" />
          </div>
          <div>
            <label for="filtro-hasta">{{ t("audit.dateTo") }}</label>
            <input id="filtro-hasta" v-model="filtros.date_to" type="date" :min="filtros.date_from" />
          </div>
        </div>
        <div class="acciones-filtro">
          <button type="submit">{{ t("audit.applyFilters") }}</button>
          <button type="button" @click="limpiarFiltros">{{ t("audit.clearFilters") }}</button>
        </div>
      </fieldset>
    </form>
    <p role="status">{{ cargando ? t("audit.loading") : error ? "" : t("audit.total", { count: total }) }}</p>
    <p v-if="error" role="alert" class="error">{{ t(error) }}</p>
    <p v-else-if="!cargando && !registros.length">{{ t("audit.empty") }}</p>

    <ol class="registros" :aria-label="t('audit.title')">
      <li v-for="registro in registros" :key="registro.id">
        <header class="cabecera">
          <h3>{{ tituloRegistro(registro) }}</h3>
          <time :datetime="registro.timestamp">{{ formatearFecha(registro.timestamp) }} {{ formatearHora(registro.timestamp) }}</time>
        </header>
        <dl class="metadatos">
          <div>
            <dt>{{ t("audit.actor") }}</dt>
            <dd>{{ registro.user === null ? t("audit.noUser") : `#${registro.user}` }}</dd>
          </div>
          <div v-if="registro.role">
            <dt>{{ t("users.role") }}</dt>
            <dd>{{ t(`roles.${registro.role}`) }}</dd>
          </div>
          <div>
            <dt>{{ t("audit.entity") }}</dt>
            <dd>{{ nombreEntidad(registro) }}<template v-if="registro.entity_id"> #{{ registro.entity_id }}</template></dd>
          </div>
        </dl>
        <p v-if="resumen(registro)" class="resumen">{{ resumen(registro) }}</p>
        <details v-if="Object.keys(registro.changes).length" open>
          <summary>{{ t("audit.changes") }}</summary>
          <div class="tabla-cambios" tabindex="0" role="region" :aria-label="t('audit.changes')">
            <table>
              <thead>
                <tr>
                  <th scope="col">{{ t("audit.field") }}</th>
                  <th v-if="registro.action_type !== 'create'" scope="col">{{ t("audit.before") }}</th>
                  <th scope="col">{{ t(registro.action_type === 'create' ? "audit.createdValue" : "audit.after") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(cambio, campo) in registro.changes" :key="campo">
                  <th scope="row">{{ nombreCampo(campo, registro.entity) }}</th>
                  <td v-if="registro.action_type !== 'create'">{{ valor(cambio.old, campo) }}</td>
                  <td>{{ valor(cambio.new, campo) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
        <p v-else>{{ t("audit.noChanges") }}</p>
      </li>
    </ol>

    <div class="paginacion">
      <button type="button" :disabled="cargando || error || !anterior" @click="cargar(pagina - 1)">{{ t("audit.previous") }}</button>
      <span>{{ t("audit.page", { page: pagina }) }}</span>
      <button type="button" :disabled="cargando || error || !siguiente" @click="cargar(pagina + 1)">{{ t("audit.next") }}</button>
    </div>
  </section>
</template>

<style scoped>
.bitacora { margin-block: 24px; min-width: 0; overflow-wrap: anywhere; }
.filtros { margin-block: 20px; padding: 20px; border: 1px solid var(--color-divisor); border-radius: 12px; background: var(--color-superficie); }
fieldset { margin: 0; padding: 0; border: 0; min-width: 0; }
legend { margin-bottom: 16px; padding: 0; font-weight: 600; color: var(--color-enlace); }
.campos-filtro { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.campos-filtro > div { display: grid; gap: 8px; min-width: 0; }
input, select { width: 100%; min-width: 0; min-height: 44px; padding: 10px 12px; border: 1px solid var(--color-borde); border-radius: 7px; font: inherit; }
.acciones-filtro { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }
button[type="submit"] { background: var(--color-header); color: #ffffff; }
.cabecera, .paginacion { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
.registros { list-style: none; padding: 0; }
.registros li { margin-block: 16px; padding: 20px; border: 1px solid var(--color-divisor); border-radius: 12px; background: var(--color-superficie); }
h2, h3 { margin-block: 0 12px; color: var(--color-enlace); }
time, dt { color: var(--color-secundario); font-size: 13px; }
.metadatos { display: flex; flex-wrap: wrap; gap: 16px 32px; }
.metadatos div { min-width: 0; }
dd { margin: 4px 0 0; }
button { min-height: 44px; padding: 10px 12px; border: 1px solid var(--color-borde); border-radius: 7px; background: var(--color-control); color: var(--color-texto); font: inherit; cursor: pointer; }
button:disabled { cursor: default; }
summary { min-height: 44px; padding-block: 12px; cursor: pointer; }
.resumen { line-height: 1.6; }
.tabla-cambios { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
th, td { padding: 12px 8px; border-bottom: 1px solid var(--color-divisor); text-align: start; vertical-align: top; white-space: pre-wrap; overflow-wrap: anywhere; }
thead th { color: var(--color-secundario); font-size: 13px; }
tbody th { font-weight: 600; }
.error { color: var(--color-error); }
@media (max-width: 560px) { .campos-filtro { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 480px) { .registros li, .filtros { padding: 16px; } }
</style>
