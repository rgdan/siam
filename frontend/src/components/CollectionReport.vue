
<script setup>
import { computed, ref, onMounted, watch } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import messages from "./collectionReportMessages.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t, locale } = useI18n({ messages, useScope: "local" })

// Filtros originales de Jorge.
const filters = ref({
  state: null,
  object_type: null,
  collection: null,
})

const options = ref({
  object_types: [],
  collections: [],
})

const report = ref(null)
const busy = ref(false)
const failure = ref(false)

const groups = [
  { key: "by_state", title: "byState" },
  { key: "by_object_type", title: "byType" },
  { key: "by_collection", title: "byCollection" },
]

// SIAM-29: exportación de colecciones.
const puedeExportar = ref(false)
const descargando = ref("")
const errorExportacion = ref(false)

const textosExportacion = {
  es: {
    titulo: "Exportar reporte",
    pdf: "Descargar PDF",
    excel: "Descargar Excel",
    descargando: "Generando archivo...",
    error: "No se pudo descargar el archivo. Intentá nuevamente.",
    sinDatos: "No hay piezas disponibles para exportar.",
  },
  en: {
    titulo: "Export report",
    pdf: "Download PDF",
    excel: "Download Excel",
    descargando: "Generating file...",
    error: "The file could not be downloaded. Please try again.",
    sinDatos: "No pieces are available for export.",
  },
}

function textoExportacion(clave) {
  const idioma = locale.value === "en" ? "en" : "es"
  return textosExportacion[idioma][clave]
}

// Al modificar filtros, se invalida el reporte anterior.
watch(
  filters,
  () => {
    report.value = null
    errorExportacion.value = false
  },
  { deep: true }
)

function filterValues(key) {
  const values = options.value[
    key === "object_type" ? "object_types" : "collections"
  ]

  return [
    ...new Set([
      ...values,
      ...(filters.value[key] === null ? [] : [filters.value[key]]),
    ]),
  ].sort()
}

// Construye los parámetros que utilizan el reporte y la exportación.
function crearConsulta(valores) {
  const query = new URLSearchParams()

  for (const [key, value] of Object.entries(valores)) {
    if (value !== null && value !== undefined) {
      query.set(key, value)
    }
  }

  return query.toString()
}

// SIAM-29: comprueba si la cuenta puede exportar.
// El backend vuelve a verificar los permisos al descargar.
async function comprobarExportacion() {
  try {
    const response = await solicitar("auth/me/")

    if (!response.ok) {
      puedeExportar.value = false
      return
    }

    const usuario = await response.json()

    puedeExportar.value = (
      usuario.role === "administrador_general" &&
      usuario.permissions?.includes("reportes.exportar") === true
    )
  } catch {
    puedeExportar.value = false
  }
}

// Consulta original del reporte de colecciones.
async function generate() {
  if (busy.value || descargando.value) return

  busy.value = true
  failure.value = false
  errorExportacion.value = false
  report.value = null

  try {
    const query = crearConsulta(filters.value)

    const ruta = (
      "collection/report/" +
      (query ? `?${query}` : "")
    )

    const response = await solicitar(ruta)

    if (response.status === 401) {
      emit("sesion-expirada")
      return
    }

    if (response.status === 403) {
      emit("sin-acceso")
      return
    }

    if (!response.ok) {
      throw new Error("No se pudo generar el reporte")
    }

    report.value = await response.json()
    options.value = report.value.available_filters

  } catch {
    failure.value = true
  } finally {
    busy.value = false
  }
}

// SIAM-29: solo se exportan reportes con piezas.
const puedeDescargar = computed(() => {
  return (
    puedeExportar.value &&
    report.value !== null &&
    report.value.total > 0 &&
    !busy.value &&
    !descargando.value
  )
})

// SIAM-29: descarga PDF o Excel respetando los filtros aplicados.
async function descargarReporte(formato) {
  if (!puedeDescargar.value) return
  if (!["pdf", "xlsx"].includes(formato)) return

  descargando.value = formato
  errorExportacion.value = false

  try {
    // Usamos los filtros del reporte generado, no otros.
    const query = crearConsulta(report.value.filters)

    const ruta = (
      `reports/export/collection/${formato}/` +
      (query ? `?${query}` : "")
    )

    const response = await solicitar(ruta)

    if (response.status === 401) {
      emit("sesion-expirada")
      return
    }

    if (response.status === 403) {
      emit("sin-acceso")
      return
    }

    if (!response.ok) {
      throw new Error("Error al generar el archivo")
    }

    const archivo = await response.blob()

    if (archivo.size === 0) {
      throw new Error("Archivo vacío")
    }

    const urlTemporal = URL.createObjectURL(archivo)
    const enlace = document.createElement("a")

    enlace.href = urlTemporal
    enlace.download = (
      `SIAM_collection_${new Date().toISOString().slice(0, 10)}.${formato}`
    )

    document.body.appendChild(enlace)
    enlace.click()
    enlace.remove()

    setTimeout(() => {
      URL.revokeObjectURL(urlTemporal)
    }, 1000)

  } catch {
    errorExportacion.value = true
  } finally {
    descargando.value = ""
  }
}

const number = (value) =>
  new Intl.NumberFormat(locale.value).format(value)

onMounted(() => {
  generate()
  comprobarExportacion()
})
</script>

<template>
  <section class="report" :aria-busy="busy">
    <h2>{{ t("title") }}</h2>

    <!-- Filtros originales del reporte de colecciones -->
    <form @submit.prevent="generate">
      <fieldset :disabled="busy || Boolean(descargando)">
        <div>
          <label for="report-state">
            {{ t("state") }}
          </label>

          <select
            id="report-state"
            v-model="filters.state"
          >
            <option :value="null">
              {{ t("allStates") }}
            </option>

            <option
              v-for="state in [
                'displayed',
                'stored',
                'loaned',
                'missing',
                'stolen',
                'lost',
                'decommissioned'
              ]"
              :key="state"
              :value="state"
            >
              {{ t(state) }}
            </option>
          </select>
        </div>

        <div>
          <label for="report-type">
            {{ t("objectType") }}
          </label>

          <select
            id="report-type"
            v-model="filters.object_type"
          >
            <option :value="null">
              {{ t("allTypes") }}
            </option>

            <option
              v-for="value in filterValues('object_type')"
              :key="value"
              :value="value"
            >
              {{ value || t("unassignedType") }}
            </option>
          </select>
        </div>

        <div>
          <label for="report-collection">
            {{ t("collection") }}
          </label>

          <select
            id="report-collection"
            v-model="filters.collection"
          >
            <option :value="null">
              {{ t("allCollections") }}
            </option>

            <option
              v-for="value in filterValues('collection')"
              :key="value"
              :value="value"
            >
              {{ value || t("unassignedCollection") }}
            </option>
          </select>
        </div>

        <button type="submit">
          {{ t("generate") }}
        </button>
      </fieldset>
    </form>

    <p v-if="busy" role="status">
      {{ t("loading") }}
    </p>

    <p v-else-if="failure" role="alert" class="error">
      {{ t("error") }}
    </p>

    <p v-else-if="!report" role="status">
      {{ t("pending") }}
    </p>

    <template v-if="report">
      <p>
        {{ t("generatedAt") }}:
        <time :datetime="report.generated_at">
          {{ new Date(report.generated_at).toLocaleString(locale) }}
        </time>
      </p>

      <p class="report-total" role="status">
        {{ t("total") }}:
        <strong data-testid="report-total">
          {{ number(report.total) }}
        </strong>
      </p>

      <p v-if="!report.total" role="status">
        {{ t("empty") }}
      </p>

      <!-- SIAM-29: exportación exclusiva del administrador general -->
      <section
        v-if="puedeExportar"
        class="report-export"
        :aria-label="textoExportacion('titulo')"
      >
        <h3>{{ textoExportacion("titulo") }}</h3>

        <div class="export-actions">
          <button
            type="button"
            :disabled="!puedeDescargar"
            @click="descargarReporte('pdf')"
          >
            {{
              descargando === "pdf"
                ? textoExportacion("descargando")
                : textoExportacion("pdf")
            }}
          </button>

          <button
            type="button"
            :disabled="!puedeDescargar"
            @click="descargarReporte('xlsx')"
          >
            {{
              descargando === "xlsx"
                ? textoExportacion("descargando")
                : textoExportacion("excel")
            }}
          </button>
        </div>

        <p v-if="report.total === 0" class="export-help">
          {{ textoExportacion("sinDatos") }}
        </p>

        <p
          v-if="errorExportacion"
          class="error"
          role="alert"
        >
          {{ textoExportacion("error") }}
        </p>
      </section>

      <!-- Resultados originales de Jorge -->
      <div class="report-groups">
        <section
          v-for="group in groups"
          :key="group.key"
          :data-group="group.key"
        >
          <h3>{{ t(group.title) }}</h3>

          <dl>
            <div
              v-for="(count, name) in report[group.key]"
              :key="name"
              :data-category="name"
            >
              <dt>
                {{
                  group.key === "by_state"
                    ? t(name)
                    : name ||
                      t(
                        group.key === "by_collection"
                          ? "unassignedCollection"
                          : "unassignedType"
                      )
                }}
              </dt>

              <dd>{{ number(count) }}</dd>
            </div>
          </dl>
        </section>
      </div>
    </template>
  </section>
</template>

<style scoped>
.report {
  color: var(--color-texto);
  overflow-wrap: anywhere;
  min-width: 0;
}

h2 {
  margin-top: 0;
}

fieldset {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: end;
  border: 0;
  padding: 0;
  min-width: 0;
}

fieldset > div {
  flex: 1 1 180px;
  min-width: 0;
}

label {
  display: block;
  margin-bottom: 8px;
}

select,
button {
  box-sizing: border-box;
  max-width: 100%;
  min-height: 44px;
  padding: 10px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  background: var(--color-control);
  color: var(--color-texto);
  font: inherit;
}

select {
  width: 100%;
}

button {
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.report-total {
  font-size: 20px;
}

.error {
  color: var(--color-error);
}

.report-groups {
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, 240px), 1fr)
  );
  gap: 16px;
}

.report-groups section {
  min-width: 0;
  padding: 16px;
  background: var(--color-superficie);
  border: 1px solid var(--color-borde);
  border-radius: 12px;
}

.report-groups h3 {
  margin-top: 0;
}

dl {
  margin: 0;
}

dl > div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-block: 12px;
}

dd {
  margin: 0;
  font-weight: bold;
}

/* SIAM-29: botones PDF y Excel */
.report-export {
  margin: 20px 0;
  padding: 16px;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-superficie);
}

.report-export h3 {
  margin: 0 0 14px;
  font-size: 17px;
}

.export-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.export-actions button {
  flex: 1 1 160px;
  background: var(--color-header);
  color: #ffffff;
}

.export-help {
  margin: 12px 0 0;
  font-size: 13px;
}

@media (max-width: 600px) {
  .export-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .export-actions button {
    width: 100%;
  }
}
</style>
