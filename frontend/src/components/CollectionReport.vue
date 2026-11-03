<script setup>
import { ref, onMounted, watch } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import messages from "./collectionReportMessages.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t, locale } = useI18n({ messages, useScope: "local" })
const filters = ref({ state: null, object_type: null, collection: null })
const options = ref({ object_types: [], collections: [] })
const report = ref(null), busy = ref(false), failure = ref(false)
const groups = [
  { key: "by_state", title: "byState" },
  { key: "by_object_type", title: "byType" },
  { key: "by_collection", title: "byCollection" },
]
watch(filters, () => { report.value = null }, { deep: true })
function filterValues(key) {
  const values = options.value[key === 'object_type' ? 'object_types' : 'collections']
  return [...new Set([...values, ...(filters.value[key] === null ? [] : [filters.value[key]])])].sort()
}
async function generate() {
  if (busy.value) return
  busy.value = true
  failure.value = false
  report.value = null
  try {
    const query = new URLSearchParams()
    for (const [key, value] of Object.entries(filters.value)) if (value !== null) query.set(key, value)
    const response = await solicitar(`collection/report/?${query}`)
    if (response.status === 401) emit("sesion-expirada")
    if (response.status === 403) emit("sin-acceso")
    if (!response.ok) throw new Error()
    report.value = await response.json()
    options.value = report.value.available_filters
  } catch { failure.value = true }
  finally { busy.value = false }
}
const number = value => new Intl.NumberFormat(locale.value).format(value)
onMounted(generate)
</script>

<template>
  <section class="report" :aria-busy="busy">
    <h2>{{ t('title') }}</h2>
    <form @submit.prevent="generate">
      <fieldset :disabled="busy">
        <div>
          <label for="report-state">{{ t('state') }}</label>
          <select id="report-state" v-model="filters.state">
            <option :value="null">{{ t('allStates') }}</option>
            <option v-for="state in ['displayed', 'stored', 'loaned', 'missing', 'stolen', 'lost', 'decommissioned']" :key="state" :value="state">{{ t(state) }}</option>
          </select>
        </div>
        <div>
          <label for="report-type">{{ t('objectType') }}</label>
          <select id="report-type" v-model="filters.object_type">
            <option :value="null">{{ t('allTypes') }}</option>
            <option v-for="value in filterValues('object_type')" :key="value" :value="value">{{ value || t('unassignedType') }}</option>
          </select>
        </div>
        <div>
          <label for="report-collection">{{ t('collection') }}</label>
          <select id="report-collection" v-model="filters.collection">
            <option :value="null">{{ t('allCollections') }}</option>
            <option v-for="value in filterValues('collection')" :key="value" :value="value">{{ value || t('unassignedCollection') }}</option>
          </select>
        </div>
        <button>{{ t('generate') }}</button>
      </fieldset>
    </form>
    <p v-if="busy" role="status">{{ t('loading') }}</p>
    <p v-else-if="failure" role="alert" class="error">{{ t('error') }}</p>
    <p v-else-if="!report" role="status">{{ t('pending') }}</p>
    <template v-if="report">
      <p>{{ t('generatedAt') }}: <time :datetime="report.generated_at">{{ new Date(report.generated_at).toLocaleString(locale) }}</time></p>
      <p class="report-total" role="status">{{ t('total') }}: <strong data-testid="report-total">{{ number(report.total) }}</strong></p>
      <p v-if="!report.total" role="status">{{ t('empty') }}</p>
      <div class="report-groups">
        <section v-for="group in groups" :key="group.key" :data-group="group.key">
          <h3>{{ t(group.title) }}</h3>
          <dl>
            <div v-for="(count, name) in report[group.key]" :key="name" :data-category="name">
              <dt>{{ group.key === 'by_state' ? t(name) : name || t(group.key === 'by_collection' ? 'unassignedCollection' : 'unassignedType') }}</dt>
              <dd>{{ number(count) }}</dd>
            </div>
          </dl>
        </section>
      </div>
    </template>
  </section>
</template>

<style scoped>
.report { color: var(--color-texto); overflow-wrap: anywhere; min-width: 0; }
h2 { margin-top: 0; }
fieldset { display: flex; flex-wrap: wrap; gap: 16px; align-items: end; border: 0; padding: 0; min-width: 0; }
fieldset > div { flex: 1 1 180px; min-width: 0; }
label { display: block; margin-bottom: 8px; }
select, button { box-sizing: border-box; max-width: 100%; min-height: 44px; padding: 10px; border: 1px solid var(--color-borde); border-radius: 6px; background: var(--color-control); color: var(--color-texto); font: inherit; }
select { width: 100%; }
button { cursor: pointer; }
button:disabled { opacity: 0.6; cursor: wait; }
.report-total { font-size: 20px; }
.error { color: var(--color-error); }
.report-groups { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 16px; }
.report-groups section { min-width: 0; padding: 16px; background: var(--color-superficie); border: 1px solid var(--color-borde); border-radius: 12px; }
.report-groups h3 { margin-top: 0; }
dl { margin: 0; }
dl > div { display: flex; justify-content: space-between; gap: 16px; margin-block: 12px; }
dd { margin: 0; font-weight: bold; }
</style>
