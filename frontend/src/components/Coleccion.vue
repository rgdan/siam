<script setup>
import { computed, ref, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar, enviar } from "../api.js"
import CollectionReport from "./CollectionReport.vue"
import messages from "./collectionMessages.js"
const props = defineProps({ usuario: Object })
const canManageCollection = computed(() => props.usuario?.permissions?.includes("piezas.actualizar"))
const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t, te, locale } = useI18n({ messages, useScope: "local" })
const fields = [
  "title",
  "collection",
  "object_type",
  "author_maker",
  "date_period",
  "subject",
  "materials_techniques",
  "inscriptions_marks",
  "distinguishing_features",
]
const label = (key) =>
  t(key === "title" ? "pieceTitle" : key === "photos" ? "photosField" : key)
const pieces = ref([]),
  selected = ref(null),
  mode = ref("list"),
  filter = ref("")
const form = ref({}),
  errors = ref({}),
  busy = ref(false),
  notice = ref(""),
  failure = ref(false)
const photoResults = ref([]),
  enlarged = ref(null),
  dialog = ref(null)
const photoToDelete = ref(null),
  deleteDialog = ref(null),
  deleteFailure = ref(false)
async function json(response) {
  if (response.status === 401) emit("sesion-expirada")
  if (response.status === 403) emit("sin-acceso")
  const data = await response.json()
  if (!response.ok) {
    errors.value = data
    throw new Error()
  }
  return data
}
async function load() {
  busy.value = true
  failure.value = false
  try {
    pieces.value = await json(
      await solicitar(`pieces/${filter.value ? `?state=${filter.value}` : ""}`),
    )
  } catch {
    failure.value = true
  } finally {
    busy.value = false
  }
}
async function detail(id) {
  selected.value = await json(await solicitar(`pieces/${id}/`))
  mode.value = "detail"
  errors.value = {}
}
async function open(id, editing = false) {
  busy.value = true
  failure.value = false
  notice.value = ""
  photoResults.value = []
  try {
    await detail(id)
    if (editing && (!selected.value.decommissioned || canManageCollection.value)) edit()
  } catch {
    failure.value = true
  } finally {
    busy.value = false
  }
}
function cancelEdit() {
  mode.value = mode.value === "new" ? "list" : "detail"
  errors.value = {}
}
function backToCollection() {
  mode.value = "list"
  load()
}
function edit(create = false) {
  mode.value = create ? "new" : "edit"
  errors.value = {}
  notice.value = ""
  form.value = create
    ? Object.fromEntries([...fields, "measurement_value"].map((f) => [f, ""]))
    : Object.fromEntries(
        [...fields, "measurement_value", "measurement_unit", "state", "location"].map((f) => [
          f,
          selected.value[f],
        ]),
      )
  if (create) Object.assign(form.value, { measurement_unit: "cm", state: "stored", location: "" })
}
function validate() {
  errors.value = {}
  for (const field of fields.filter(field => field !== "collection"))
    if (!String(form.value[field] || "").trim())
      errors.value[field] = "required"
  const value = String(form.value.measurement_value)
  if (!/^\d+(\.\d{1,4})?$/.test(value) || Number(value) <= 0)
    errors.value.measurement_value = "positive"
  if (form.value.state === "displayed" && !String(form.value.location || "").trim())
    errors.value.location = "required"
  return !Object.keys(errors.value).length
}
async function save() {
  if (busy.value || (mode.value === "edit" && selected.value.decommissioned) || !validate()) return
  errors.value = {}
  failure.value = false
  busy.value = true
  notice.value = ""
  try {
    const creating = mode.value === "new"
    const data = { ...form.value }
    if (!creating && ['stolen', 'lost', 'loaned'].includes(selected.value.state)) {
      delete data.state
      delete data.location
    }
    const saved = await json(
      await enviar(
        creating ? "pieces/" : `pieces/${selected.value.id}/`,
        data,
        creating ? "POST" : "PATCH",
      ),
    )
    await detail(saved.id)
    await load()
    notice.value = "saved"
  } catch {
    failure.value = true
  } finally {
    busy.value = false
  }
}
function fieldError(field) {
  const value = Array.isArray(errors.value[field])
    ? errors.value[field][0]
    : errors.value[field]
  return t(["required", "positive", "invalid_loan_period", "invalid_date", "recipient_too_long", "future_date", "invalid_state", "confirmation_required"].includes(value) ? value : "invalid")
}
async function upload(event) {
  const input = event.target,
    files = [...input.files]
  if (!files.length) return
  busy.value = true
  photoResults.value = []
  failure.value = false
  try {
    for (const file of files) {
      if (file.size > 5 * 1024 * 1024) {
        photoResults.value.push({ name: file.name, code: "too_large" })
        continue
      }
      const content = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result.split(",")[1])
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
      const result = await json(
        await enviar(`pieces/${selected.value.id}/photos/`, {
          photos: [{ name: file.name, content }],
        }),
      )
      const item = result.results[0]
      const errorText = JSON.stringify(item.errors || {})
      const code = [
        "too_large",
        "invalid_format",
        "invalid_image",
        "upload_failed",
      ].find((code) => errorText.includes(code))
      photoResults.value.push({
        name: file.name,
        code: item.id ? "attached" : code || "invalid_image",
      })
    }
    selected.value = await json(await solicitar(`pieces/${selected.value.id}/`))
  } catch {
    failure.value = true
  } finally {
    input.value = ""
    busy.value = false
  }
}
function showPhoto(photo) {
  enlarged.value = photo
  dialog.value.showModal()
}
function confirmPhotoDelete(photo) {
  if (busy.value) return
  photoToDelete.value = photo
  deleteFailure.value = false
  deleteDialog.value.showModal()
}
async function deletePhoto() {
  if (busy.value || !photoToDelete.value) return
  busy.value = true
  deleteFailure.value = false
  notice.value = ""
  try {
    const id = photoToDelete.value.id
    await json(await enviar(`pieces/${selected.value.id}/photos/${id}/`, {}, "DELETE"))
    selected.value.photos = selected.value.photos.filter(photo => photo.id !== id)
    deleteDialog.value.close()
    photoToDelete.value = null
    notice.value = "photoDeleted"
  } catch {
    deleteFailure.value = true
  } finally {
    busy.value = false
  }
}
async function movePhoto(index, direction) {
  const target = index + direction
  if (busy.value || target < 0 || target >= selected.value.photos.length) return
  const photos = [...selected.value.photos]
  const photo = photos.splice(index, 1)[0]
  photos.splice(target, 0, photo)
  busy.value = true
  failure.value = false
  notice.value = ""
  try {
    await json(await enviar(`pieces/${selected.value.id}/photos/order/`, { photos: photos.map(photo => photo.id) }, "PATCH"))
    selected.value.photos = photos
    notice.value = "photoOrderSaved"
  } catch {
    failure.value = true
  } finally {
    busy.value = false
  }
}
const loanDialog = ref(null)
const loanForm = ref({ recipient: "", start_date: "", end_date: "" })
const invalidLoanPeriod = computed(() => loanForm.value.start_date && loanForm.value.end_date && loanForm.value.end_date < loanForm.value.start_date)
const loanBlockReason = computed(() => {
  if (selected.value?.decommissioned || selected.value?.state === 'decommissioned') return 'cannot_loan_decommissioned'
  if (selected.value?.state === 'stolen') return 'cannot_loan_stolen'
  if (selected.value?.state === 'lost') return 'cannot_loan_lost'
  return ''
})
function beginLoan() {
  loanForm.value = { recipient: "", start_date: "", end_date: "" }
  errors.value = {}
  failure.value = false
  loanDialog.value.showModal()
}
function loanFailure() {
  const code = errors.value.detail
  return t(typeof code === 'string' && te(code) ? code : 'error')
}
async function saveLoan(returning = false) {
  if (busy.value || (!returning && invalidLoanPeriod.value)) return
  busy.value = true
  errors.value = {}
  failure.value = false
  notice.value = ""
  try {
    await json(await enviar(`pieces/${selected.value.id}/${returning ? 'return' : 'loan'}/`, returning ? {} : loanForm.value))
    loanDialog.value.close()
    selected.value = await json(await solicitar(`pieces/${selected.value.id}/`))
    form.value.state = selected.value.state
    form.value.location = selected.value.location
    notice.value = returning ? "loanReturned" : "loanSaved"
  } catch { failure.value = true }
  finally { busy.value = false }
}
function loanDate(value) {
  return value ? new Date(`${value}T12:00:00`).toLocaleDateString(locale.value) : t('notRecorded')
}
const missingDialog = ref(null), missingForm = ref({})
function today() {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'America/Costa_Rica', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date())
  const part = key => parts.find(value => value.type === key).value
  return `${part('year')}-${part('month')}-${part('day')}`
}
function eventDate(value) {
  return new Date(`${value}T12:00:00`).toLocaleDateString(locale.value)
}
function beginMissing() {
  missingForm.value = { state: "", event_date: "", observations: "", confirmed: false }
  errors.value = {}
  failure.value = false
  missingDialog.value.showModal()
}
async function saveMissing() {
  if (busy.value) return
  busy.value = true
  failure.value = false
  try {
    await json(await enviar(`pieces/${selected.value.id}/missing/`, missingForm.value))
    missingDialog.value.close()
    selected.value = await json(await solicitar(`pieces/${selected.value.id}/`))
    form.value.state = selected.value.state
    form.value.location = selected.value.location
    notice.value = "saved"
  } catch { failure.value = true }
  finally { busy.value = false }
}
const recoveryDialog = ref(null)
function beginRecovery() {
  errors.value = {}
  failure.value = false
  recoveryDialog.value.showModal()
}
async function recoverPiece() {
  if (busy.value) return
  busy.value = true
  failure.value = false
  notice.value = ""
  try {
    const reactivating = selected.value.decommissioned
    await json(await enviar(`pieces/${selected.value.id}/${reactivating ? 'reactivate' : 'recover'}/`))
    recoveryDialog.value.close()
    selected.value = await json(await solicitar(`pieces/${selected.value.id}/`))
    form.value.state = selected.value.state
    form.value.location = selected.value.location
    notice.value = reactivating ? "pieceReactivated" : "pieceRecovered"
  } catch { failure.value = true }
  finally { busy.value = false }
}
const lifecycleDialog = ref(null), reason = ref("")
function beginDecommission() {
  failure.value = false
  reason.value = ""
  errors.value = {}
  lifecycleDialog.value.showModal()
}
async function decommission() {
  if (busy.value || !reason.value.trim()) return
  busy.value = true
  failure.value = false
  try {
    await json(await enviar(`pieces/${selected.value.id}/decommission/`, { reason: reason.value, confirmed: true }))
    lifecycleDialog.value.close()
    await detail(selected.value.id)
    notice.value = "saved"
  } catch { failure.value = true }
  finally { busy.value = false }
}
function openReport() {
  notice.value = ""
  failure.value = false
  mode.value = "report"
}
onMounted(load)
</script>
<template>
  <section class="collection" :class="{ 'collection-list': mode === 'list' }" :aria-busy="busy">
    <p v-if="busy" role="status">{{ t("loading") }}</p>
    <p v-if="notice" role="status">{{ t(notice) }}</p>
    <p v-if="failure" role="alert" class="error">{{ t("error") }}</p>
    <template v-if="mode === 'report'">
      <button class="back-link" @click="backToCollection">{{ t('back') }}</button>
      <CollectionReport @sesion-expirada="emit('sesion-expirada')" @sin-acceso="emit('sin-acceso')" />
    </template>
    <template v-else-if="mode === 'list'">
      <header class="collection-heading">
        <div>
          <h2>{{ t("listTitle") }}</h2>
          <p v-if="!busy && !failure" class="piece-count">{{ t(filter ? "filteredCount" : "pieceCount", { count: pieces.length }) }}</p>
        </div>
        <div class="list-actions">
          <button v-if="props.usuario?.permissions?.includes('colecciones.generar_reportes')" :disabled="busy" @click="openReport">{{ t('report') }}</button>
          <button class="refresh-list" :disabled="busy" :aria-label="t('refresh')" :title="t('refresh')" @click="load">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 7v5h-5M4 17v-5h5" /><path d="M6.1 7a7 7 0 0 1 11.5-1L20 9M4 15l2.4 3a7 7 0 0 0 11.5-1" /></svg>
          </button>
          <button class="new-piece" :disabled="busy" @click="edit(true)">
            <span aria-hidden="true">+</span>{{ t("new") }}
          </button>
        </div>
      </header>
      <div class="collection-table" role="region" :aria-label="t('listTitle')" tabindex="0">
        <table>
          <thead>
            <tr>
              <th scope="col" class="identifier-column">{{ t("id") }}</th>
              <th scope="col" class="title-column">{{ t("pieceTitle") }}</th>
              <th scope="col">{{ t("typeColumn") }}</th>
              <th scope="col">{{ t("authorColumn") }}</th>
              <th scope="col">
                <select id="state-filter" v-model="filter" class="table-state-filter" :aria-label="t('state')" :disabled="busy" @change="load">
                  <option value="">{{ t("state") }}</option>
                  <option value="stored">{{ t("stored") }}</option>
                  <option value="displayed">{{ t("displayed") }}</option>
                  <option value="stolen">{{ t("stolen") }}</option>
                  <option value="lost">{{ t("lost") }}</option>
                  <option value="decommissioned">{{ t("decommissioned") }}</option>
                  <option value="loaned">{{ t("loaned") }}</option>
                </select>
              </th>
              <th scope="col">{{ t("location") }}</th>
              <th scope="col" class="actions-column"><span class="sr-only">{{ t("edit") }}</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="piece in pieces" :key="piece.id">
              <td><span class="piece-identifier" :title="piece.identifier">{{ piece.identifier }}</span></td>
              <th scope="row">
                <button class="piece-title" :disabled="busy" @click="open(piece.id)">{{ piece.title }}</button>
              </th>
              <td>{{ piece.object_type }}</td>
              <td>{{ piece.author_maker }}</td>
              <td><span class="piece-state" :class="piece.state">{{ t(piece.state) }}</span></td>
              <td>{{ piece.location || t("noLocation") }}</td>
              <td class="row-actions">
                <button v-if="!piece.decommissioned || canManageCollection" class="edit-piece" :disabled="busy" :aria-label="t('editPiece', { title: piece.title })" :title="t('edit')" @click="open(piece.id, true)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M13.5 5.5 18.5 10.5M4 20l4.5-1 12-12a2.1 2.1 0 0 0-3-3l-12 12L4 20Z" />
                    <path d="M12 4H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-7" />
                  </svg>
                </button>
              </td>
            </tr>
            <tr v-if="!pieces.length">
              <td colspan="7" class="empty-collection">{{ t(busy ? "loading" : failure ? "error" : "empty") }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
    <template v-else-if="mode === 'new' || mode === 'edit'">
      <button class="back-link" :disabled="busy" @click="backToCollection">{{ t("back") }}</button>
      <header class="editor-heading">
        <h2>{{ t(mode === "new" ? "new" : "editHeading") }}</h2>
        <p>{{ mode === 'new' ? t('newDescription') : selected.title }}</p>
      </header>
      <form class="piece-editor" novalidate @submit.prevent="save()">
        <div class="editor-layout">
        <section class="record-panel">
        <fieldset :disabled="busy || (mode === 'edit' && selected.decommissioned)" class="fields">
          <legend>{{ t("catalogDetails") }}</legend>
          <div v-for="field in fields" :key="field" :class="{ 'wide-field': !['title', 'object_type', 'author_maker', 'date_period'].includes(field) }">
            <label :for="field">{{ label(field) }}{{ field === 'collection' ? '' : ' *' }}</label
            ><input
              v-if="['title', 'object_type', 'author_maker', 'date_period', 'collection'].includes(field)"
              :id="field"
              v-model="form[field]"
              :required="field !== 'collection'"
              :maxlength="['title', 'collection'].includes(field) ? 200 : undefined"
              :aria-invalid="!!errors[field]"
              :aria-describedby="errors[field] ? `${field}-error` : undefined"
            /><textarea
              v-else
              :id="field"
              v-model="form[field]"
              required
              :maxlength="field === 'title' ? 200 : undefined"
              :aria-invalid="!!errors[field]"
              :aria-describedby="errors[field] ? `${field}-error` : undefined"
            />
            <p v-if="errors[field]" :id="`${field}-error`" class="error">
              {{ fieldError(field) }}
            </p>
          </div>
          <div class="measurement-fields wide-field">
            <div><label for="measurement">{{ t("measurements") }} *</label
            ><input
              id="measurement"
              v-model="form.measurement_value"
              type="number"
              min="0.0001"
              step="0.0001"
              required
              :aria-invalid="!!errors.measurement_value"
              aria-describedby="measurement-error"
            />
            <p
              v-if="errors.measurement_value"
              id="measurement-error"
              class="error"
            >
              {{ fieldError("measurement_value") }}
            </p>
            </div>
            <div><label for="unit">{{ t("measurement_unit") }}</label
            ><select id="unit" v-model="form.measurement_unit">
              <option v-for="unit in ['mm', 'cm', 'm', 'g', 'kg']" :key="unit">
                {{ unit }}
              </option>
            </select>
            </div>
          </div>
        </fieldset>
        </section>
        <aside class="editor-sidebar">
        <section class="record-panel state-editor">
        <fieldset :disabled="busy">
          <legend>{{ t("stateAndLocation") }}</legend>
          <label for="piece-state">{{ t("state") }}</label>
          <select id="piece-state" v-model="form.state" :disabled="mode === 'new' || selected.decommissioned || !['stored', 'displayed'].includes(selected.state)">
            <option v-if="mode === 'edit' && !['stored', 'displayed'].includes(selected.state)" :value="selected.state">{{ t(selected.state) }}</option>
            <option value="stored">{{ t("stored") }}</option>
            <option v-if="mode === 'edit'" value="displayed">{{ t("displayed") }}</option></select
          ><template v-if="['stored', 'displayed'].includes(form.state) && (mode === 'new' || !selected.decommissioned)"
            ><label for="location">{{ t("location") }}{{ form.state === 'displayed' ? ' *' : '' }}</label
            ><input
              id="location"
              v-model="form.location"
              maxlength="200"
              :required="form.state === 'displayed'"
              :aria-invalid="!!errors.location"
              aria-describedby="location-error"
            />
            <p v-if="errors.location" id="location-error" class="error">
              {{ fieldError("location") }}
            </p></template>
          <template v-if="mode === 'edit' && canManageCollection">
            <div class="actions state-actions">
              <button v-if="selected.state !== 'loaned'" type="button" :disabled="!!loanBlockReason" :title="loanBlockReason ? t(loanBlockReason) : undefined" @click="beginLoan">{{ t('registerLoan') }}</button>
              <button v-if="!loanBlockReason && selected.state === 'loaned'" type="button" @click="saveLoan(true)">{{ t('returnLoan') }}</button>
              <button v-if="!selected.decommissioned && !['stolen', 'lost'].includes(selected.state)" type="button" @click="beginMissing">{{ t('markMissing') }}</button>
              <button v-if="!selected.decommissioned && ['stolen', 'lost'].includes(selected.state)" type="button" @click="beginRecovery">{{ t('recoverPiece') }}</button>
              <button v-if="selected.decommissioned" type="button" @click="beginRecovery">{{ t('reactivatePiece') }}</button>
              <button v-if="!selected.decommissioned" type="button" @click="beginDecommission">{{ t('decommission') }}</button>
            </div>
            <p v-if="failure && !loanDialog?.open" class="error" role="alert">{{ loanFailure() }}</p>
          </template>
        </fieldset>
        </section>
        <section v-if="mode === 'edit' && !selected.decommissioned" class="record-panel photo-editor">
      <h3>{{ t("photos") }}</h3>
      <p v-if="selected.photos.length" class="photo-note">{{ t('photoOrderHelp') }}</p>
      <p v-if="!selected.photos.length">{{ t("noPhotos") }}</p>
      <div class="photos">
        <figure v-for="(photo, index) in selected.photos" :key="photo.id" class="editable-photo">
        <span class="photo-position">{{ index === 0 ? t('coverPhoto') : t('photoPosition', { position: index + 1 }) }}</span>
        <button
          type="button"
          :disabled="busy"
          @click="showPhoto(photo)"
        >
          <img :src="photo.data" :alt="photo.name" />
        </button>
        <figcaption>{{ photo.name }}</figcaption>
        <div class="photo-order-controls">
          <button type="button" :disabled="busy || index === 0" :aria-label="t('movePhotoEarlier', { name: photo.name })" @click="movePhoto(index, -1)"><span aria-hidden="true">‹</span></button>
          <button type="button" :disabled="busy || index === selected.photos.length - 1" :aria-label="t('movePhotoLater', { name: photo.name })" @click="movePhoto(index, 1)"><span aria-hidden="true">›</span></button>
        </div>
        <button class="delete-photo" type="button" :disabled="busy" :aria-label="t('deletePhotoNamed', { name: photo.name })" @click="confirmPhotoDelete(photo)">{{ t('deletePhoto') }}</button>
        </figure>
      </div>
      <label for="photos">{{ t("addPhotos") }}</label>
      <p id="photo-help">{{ t("photoHelp") }}</p>
      <p class="photo-note">{{ t("photosImmediate") }}</p>
      <input
        id="photos"
        type="file"
        multiple
        accept="image/jpeg,image/png,image/webp"
        :disabled="busy"
        aria-describedby="photo-help"
        @change="upload"
      />
      <ul aria-live="polite">
        <li v-for="(result, index) in photoResults" :key="index">
          {{ result.name }}: {{ t(result.code) }}
        </li>
      </ul>
        </section>
        <section class="record-panel editor-note">
          <h3>{{ t("identifier") }}</h3>
          <p v-if="mode === 'edit'" class="record-identifier">{{ selected.identifier }}</p>
          <p v-else>{{ t("identifierAssigned") }}</p>
        </section>
        </aside>
        </div>
        <footer class="editor-footer">
          <p>{{ t("requiredFields") }}</p>
          <div class="actions">
            <button type="button" :disabled="busy" @click="cancelEdit">{{ t("cancel") }}</button>
            <button class="primary-action" :disabled="busy || (mode === 'edit' && selected.decommissioned)">{{ t("save") }}</button>
          </div>
        </footer>
      </form>
    </template>
    <template v-else-if="selected">
      <button class="back-link" :disabled="busy" @click="backToCollection">{{ t("back") }}</button>
      <article class="piece-sheet">
        <header class="piece-heading">
          <p class="piece-category">{{ selected.object_type || t('notRecorded') }}</p>
          <h2>{{ selected.title }}</h2>
          <p class="piece-attribution">{{ selected.author_maker || t('notRecorded') }}<span v-if="selected.date_period"> · {{ selected.date_period }}</span></p>
          <span class="piece-state" :class="selected.state">{{ t(selected.state) }}</span>
          <span v-if="selected.decommissioned && selected.state !== 'decommissioned'" class="inactive-piece">{{ t('decommissioned') }}</span>
        </header>
        <div class="piece-overview">
          <section class="piece-gallery" :aria-label="t('photos')">
            <button v-if="selected.photos.length" class="hero-photo" :aria-label="t('enlargePhoto')" @click="showPhoto(selected.photos[0])">
              <img :src="selected.photos[0].data" :alt="selected.photos[0].name" />
            </button>
            <div v-else class="no-photo"><p>{{ t('noPhotos') }}</p></div>
            <div v-if="selected.photos.length > 1" class="photos gallery-thumbnails">
              <button v-for="photo in selected.photos" :key="photo.id" @click="showPhoto(photo)">
                <img :src="photo.data" :alt="photo.name" />
              </button>
            </div>
          </section>
          <section class="piece-description">
            <h3>{{ t('subject') }}</h3>
            <p class="piece-subject">{{ selected.subject || t('notRecorded') }}</p>
            <dl class="piece-facts">
              <div><dt>{{ t('materials_techniques') }}</dt><dd>{{ selected.materials_techniques || t('notRecorded') }}</dd></div>
              <div><dt>{{ t('measurements') }}</dt><dd>{{ selected.measurement_value === null ? t('notRecorded') : `${selected.measurement_value} ${selected.measurement_unit}` }}</dd></div>
              <div><dt>{{ t('location') }}</dt><dd>{{ selected.location || t('noLocation') }}</dd></div>
            </dl>
          </section>
        </div>
        <section class="piece-documentation">
          <h3>{{ t('documentation') }}</h3>
          <p>{{ t('collection') }}: {{ selected.collection || t('unassignedCollection') }}</p>
          <dl class="documentation-grid">
            <div v-for="field in ['inscriptions_marks', 'distinguishing_features']" :key="field">
              <dt>{{ label(field) }}</dt><dd>{{ selected[field] || t('notRecorded') }}</dd>
            </div>
            <div class="identifier-fact"><dt>{{ t('identifier') }}</dt><dd class="record-identifier">{{ selected.identifier }}</dd></div>
          </dl>
        </section>
        <section v-if="selected.state === 'loaned' || selected.decommissioned || selected.event_date" class="piece-documentation">
          <h3 v-if="selected.state === 'loaned'">{{ t('loanDetails') }}</h3>
          <dl v-if="selected.state === 'loaned'" class="documentation-grid">
            <div><dt>{{ t('loan_to') }}</dt><dd>{{ selected.loan_to }}</dd></div>
            <div><dt>{{ t('loan_start') }}</dt><dd>{{ loanDate(selected.loan_start) }}</dd></div>
            <div><dt>{{ t('loan_end') }}</dt><dd>{{ loanDate(selected.loan_end) }}</dd></div>
          </dl>
          <dl v-if="selected.decommissioned">
            <dt>{{ t('decommissionReason') }}</dt><dd>{{ selected.decommission_reason || t('notRecorded') }}</dd>
            <dt>{{ t('recordedAt') }}</dt><dd>{{ selected.decommissioned_at ? new Date(selected.decommissioned_at).toLocaleString(locale) : t('notRecorded') }}</dd>
            <dt>{{ t('recordedBy') }}</dt><dd>{{ selected.decommissioned_user || t('notRecorded') }}</dd>
          </dl>
          <dl v-if="selected.event_date">
            <dt>{{ t('event_date') }}</dt><dd>{{ eventDate(selected.event_date) }}</dd>
            <dt>{{ t('event_observations') }}</dt><dd>{{ selected.event_observations || t('notRecorded') }}</dd>
          </dl>
        </section>
      </article>
    </template>
    <dialog ref="loanDialog" class="delete-photo-dialog" aria-labelledby="loan-heading" :aria-busy="busy" @cancel="busy && $event.preventDefault()">
      <form @submit.prevent="saveLoan(false)">
        <h3 id="loan-heading">{{ t('registerLoan') }}</h3>
        <fieldset :disabled="busy">
          <label for="loan-recipient">{{ t('loan_to') }} *</label>
          <input id="loan-recipient" v-model="loanForm.recipient" required maxlength="200" :aria-invalid="!!errors.recipient" aria-describedby="loan-recipient-error" />
          <p v-if="errors.recipient" id="loan-recipient-error" class="error">{{ fieldError('recipient') }}</p>
          <label for="loan-start">{{ t('loan_start') }} *</label>
          <input id="loan-start" v-model="loanForm.start_date" type="date" required :aria-invalid="!!errors.start_date" aria-describedby="loan-start-error" />
          <p v-if="errors.start_date" id="loan-start-error" class="error">{{ fieldError('start_date') }}</p>
          <label for="loan-end">{{ t('loan_end') }} *</label>
          <input id="loan-end" v-model="loanForm.end_date" type="date" required :min="loanForm.start_date" :aria-invalid="!!errors.end_date || !!invalidLoanPeriod" aria-describedby="loan-end-error" />
          <p v-if="errors.end_date || invalidLoanPeriod" id="loan-end-error" class="error">{{ errors.end_date ? fieldError('end_date') : t('invalid_loan_period') }}</p>
        </fieldset>
        <p v-if="failure" role="alert" class="error">{{ loanFailure() }}</p>
        <div class="actions">
          <button type="button" :disabled="busy" @click="loanDialog.close()">{{ t('cancel') }}</button>
          <button :disabled="busy">{{ t('save') }}</button>
        </div>
      </form>
    </dialog>
    <dialog ref="missingDialog" class="delete-photo-dialog" aria-labelledby="missing-heading" @cancel="busy && $event.preventDefault()">
      <form @submit.prevent="saveMissing">
        <h3 id="missing-heading">{{ t('markMissing') }}</h3>
        <fieldset :disabled="busy">
          <label for="missing-state">{{ t('state') }} *</label>
          <select id="missing-state" v-model="missingForm.state" required :aria-invalid="!!errors.state" aria-describedby="missing-state-error">
            <option disabled value="">{{ t('chooseState') }}</option>
            <option value="stolen">{{ t('stolen') }}</option><option value="lost">{{ t('lost') }}</option>
          </select>
          <p v-if="errors.state" id="missing-state-error" class="error">{{ fieldError('state') }}</p>
          <label for="event-date">{{ t('event_date') }} *</label>
          <input id="event-date" v-model="missingForm.event_date" type="date" required :max="today()" :aria-invalid="!!errors.event_date" aria-describedby="event-date-error" />
          <p v-if="errors.event_date" id="event-date-error" class="error">{{ fieldError('event_date') }}</p>
          <label for="observations">{{ t('observations') }}</label>
          <textarea id="observations" v-model="missingForm.observations" />
          <label><input v-model="missingForm.confirmed" class="confirmation" type="checkbox" required /> {{ t('missingConfirm') }}</label>
          <p v-if="errors.confirmed" class="error">{{ fieldError('confirmed') }}</p>
        </fieldset>
        <p v-if="failure" role="alert" class="error">{{ t('error') }}</p>
        <div class="actions"><button type="button" :disabled="busy" @click="missingDialog.close()">{{ t('cancel') }}</button><button :disabled="busy">{{ t('confirm') }}</button></div>
      </form>
    </dialog>
    <dialog ref="recoveryDialog" class="delete-photo-dialog" aria-labelledby="recovery-heading" @cancel="busy && $event.preventDefault()">
      <h3 id="recovery-heading">{{ t(selected?.decommissioned ? 'reactivatePiece' : 'recoverPiece') }}</h3>
      <p>{{ t(selected?.decommissioned ? 'reactivationConfirm' : 'recoveryConfirm') }}</p>
      <p v-if="failure" role="alert" class="error">{{ loanFailure() }}</p>
      <div class="actions">
        <button type="button" :disabled="busy" autofocus @click="recoveryDialog.close()">{{ t('cancel') }}</button>
        <button type="button" :disabled="busy" @click="recoverPiece">{{ t('confirm') }}</button>
      </div>
    </dialog>
    <dialog ref="lifecycleDialog" class="delete-photo-dialog" aria-labelledby="lifecycle-heading" @cancel="busy && $event.preventDefault()">
      <form @submit.prevent="decommission">
        <h3 id="lifecycle-heading">{{ t('decommission') }}</h3>
        <p>{{ t('decommissionWarning') }}</p>
        <label for="decommission-reason">{{ t('decommissionReason') }} *</label>
        <textarea id="decommission-reason" v-model="reason" required :disabled="busy" />
        <p v-if="failure" role="alert" class="error">{{ t('error') }}</p>
        <div class="actions">
          <button type="button" :disabled="busy" autofocus @click="lifecycleDialog.close()">{{ t('cancel') }}</button>
          <button :disabled="busy || !reason.trim()">{{ t('confirm') }}</button>
        </div>
      </form>
    </dialog>
    <dialog ref="deleteDialog" class="delete-photo-dialog" aria-labelledby="delete-photo-heading" :aria-busy="busy" @cancel="busy && $event.preventDefault()">
      <h3 id="delete-photo-heading">{{ t('deletePhoto') }}</h3>
      <p>{{ t('deletePhotoConfirm', { name: photoToDelete?.name }) }}</p>
      <p class="photo-note">{{ t('deletePhotoWarning') }}</p>
      <p v-if="deleteFailure" role="alert" class="error">{{ t('deletePhotoError') }}</p>
      <div class="actions">
        <button type="button" :disabled="busy" autofocus @click="deleteDialog.close()">{{ t('cancel') }}</button>
        <button class="primary-action" type="button" :disabled="busy" @click="deletePhoto">{{ t('deletePhoto') }}</button>
      </div>
    </dialog>
    <dialog
      ref="dialog"
      @click="
        (event) => {
          if (event.target === dialog) dialog.close()
        }
      "
    >
      <button @click="dialog.close()">{{ t("close") }}</button
      ><img v-if="enlarged" :src="enlarged.data" :alt="enlarged.name" />
    </dialog>
  </section>
</template>
<style scoped>
.confirmation { width: auto; min-height: auto; }
.piece-state.stolen, .piece-state.lost { color: var(--color-error); border: 1px solid currentColor; }
.collection {
  color: var(--color-texto);
  overflow-wrap: anywhere;
  min-width: 0;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 16px 0;
}
button,
input,
select,
textarea {
  font: inherit;
  box-sizing: border-box;
  min-height: 44px;
  max-width: 100%;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  padding: 10px;
  background: var(--color-control);
  color: var(--color-texto);
}
button {
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
label {
  display: block;
  margin: 12px 0 6px;
}
input,
select,
textarea {
  width: 100%;
}
textarea {
  min-height: 80px;
}
fieldset {
  border: 0;
  padding: 0;
  margin: 16px 0;
  min-width: 0;
}
.fields {
  display: grid;
  gap: 16px;
}
.fields > div {
  min-width: 0;
}
.error {
  color: var(--color-error);
}
[aria-invalid="true"] {
  border: 2px solid var(--color-error);
}
.collection-heading { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; margin-bottom: 22px; }
.collection-heading h2 { margin: 0; font-size: 32px; line-height: 1.2; letter-spacing: -0.6px; }
.piece-count { margin: 6px 0 0; color: var(--color-secundario); font-size: 13px; }
.new-piece { display: inline-flex; align-items: center; justify-content: center; gap: 12px; padding: 10px 20px; border-color: var(--color-acento); border-radius: 8px; background: var(--color-acento); color: #fff; font-size: 13px; font-weight: 600; }
.new-piece span { font-size: 20px; line-height: 1; font-weight: 400; }
.list-actions { display: flex; align-items: center; gap: 8px; }
.refresh-list { display: inline-flex; align-items: center; justify-content: center; width: 44px; padding: 10px; border: 0; background: transparent; color: var(--color-secundario); }
.refresh-list svg { width: 18px; height: 18px; }
.collection-table { position: relative; border: 1px solid var(--color-divisor); border-radius: 16px; overflow-x: auto; background: var(--color-superficie); box-shadow: 0 1px 2px #00000012; }
.collection-table table { width: 100%; min-width: 880px; border-collapse: collapse; table-layout: fixed; font-size: 13px; }
.collection-table thead { background: var(--color-header); color: #fff; }
.collection-table th, .collection-table td { text-align: start; padding: 6px 16px; border-bottom: 1px solid var(--color-divisor); }
.collection-table thead th { height: 40px; border-bottom: 0; font-size: 11px; letter-spacing: 0.6px; text-transform: uppercase; font-weight: 700; }
.table-state-filter { min-height: 44px; border: 0; border-radius: 0; padding: 0; background: var(--color-header); color: #fff; font-size: inherit; font-weight: inherit; letter-spacing: inherit; text-transform: uppercase; cursor: pointer; }
.table-state-filter option { background: var(--color-control); color: var(--color-texto); }
.collection-table tbody td { color: var(--color-secundario); }
.collection-table tbody th { font-weight: 400; }
.collection-table tbody tr:last-child > * { border-bottom: 0; }
.identifier-column { width: 13%; }
.title-column { width: 25%; }
.actions-column { width: 64px; }
.piece-identifier { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font: 11px ui-monospace, monospace; }
.piece-title { width: 100%; padding: 6px 0; text-align: start; border: 0; background: transparent; border-radius: 0; font-size: inherit; line-height: 1.5; }
.piece-state { display: inline-block; padding: 3px 8px; border-radius: 20px; font-size: 11px; line-height: 1.4; }
.piece-state.displayed { background: #effcf3; color: #17652f; }
.piece-state.stored { background: var(--color-footer); color: var(--color-secundario); }
.piece-state.loaned { color: var(--color-enlace); border: 1px solid currentColor; }
.collection-table .row-actions { padding: 4px 8px; }
.edit-piece { display: inline-flex; align-items: center; justify-content: center; min-width: 44px; padding: 10px; border: 0; background: transparent; color: var(--color-secundario); }
.edit-piece svg { width: 18px; height: 18px; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }
.collection-table .empty-collection { padding: 40px 20px; text-align: center; }
@media (hover: hover) {
  .collection-table tbody tr:hover { background: var(--color-footer); }
  .piece-title:hover { color: var(--color-enlace); text-decoration: underline; }
  .edit-piece:hover { color: var(--color-enlace); background: var(--color-footer); }
}
@media (max-width: 600px) {
  .collection-heading { align-items: flex-start; gap: 16px; }
  .collection-heading h2 { font-size: 28px; }
  .new-piece { padding-inline: 14px; }
}
dt {
  font-weight: bold;
}
dd {
  margin: 4px 0 16px;
  white-space: pre-wrap;
}
.photos {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.photos img {
  width: 100px;
  height: 100px;
  object-fit: cover;
}
.back-link { display: inline-flex; align-items: center; gap: 8px; padding: 8px 0; margin-bottom: 20px; border: 0; background: transparent; color: var(--color-secundario); font-size: 13px; }
.back-link::before { content: "\2039"; font-size: 24px; line-height: 1; }
.piece-sheet { border: 1px solid var(--color-divisor); border-radius: 16px; background: var(--color-superficie); }
.piece-heading { padding: 32px; border-bottom: 1px solid var(--color-divisor); }
.piece-category { margin: 0 0 10px; color: var(--color-secundario); font-size: 13px; }
.piece-heading h2 { max-width: 24ch; margin: 0; font-size: clamp(28px, 3vw, 40px); line-height: 1.15; letter-spacing: -0.6px; }
.piece-attribution { margin: 14px 0 18px; color: var(--color-secundario); font-size: 15px; line-height: 1.6; }
.inactive-piece { margin-left: 12px; color: var(--color-error); font-size: 12px; }
.piece-overview { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 40px; padding: 32px; }
.piece-gallery, .piece-description { min-width: 0; }
.hero-photo { display: flex; flex-direction: column; align-items: center; gap: 12px; width: 100%; padding: 16px; border: 0; background: var(--color-footer); }
.hero-photo img { display: block; width: 100%; height: 330px; object-fit: contain; }
.no-photo { display: grid; place-items: center; min-height: 280px; padding: 24px; border-radius: 8px; background: var(--color-footer); color: var(--color-secundario); }
.gallery-thumbnails { gap: 10px; margin-top: 12px; }
.gallery-thumbnails button { padding: 4px; border-color: var(--color-divisor); }
.gallery-thumbnails img { display: block; width: 64px; height: 64px; }
.piece-description h3, .piece-documentation h3 { margin: 0 0 16px; font-size: 22px; font-weight: 600; }
.piece-subject { margin: 0 0 28px; white-space: pre-wrap; font-size: 15px; line-height: 1.8; }
.piece-facts { display: grid; gap: 20px; margin: 0; }
.piece-facts dt, .documentation-grid dt { margin-bottom: 6px; color: var(--color-secundario); font-size: 12px; font-weight: 400; }
.piece-facts dd, .documentation-grid dd { margin: 0; font-size: 14px; line-height: 1.7; }
.piece-documentation { border-top: 1px solid var(--color-divisor); padding: 28px 32px; }
.documentation-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 28px; margin: 0; }
.identifier-fact { grid-column: 1 / -1; padding-top: 20px; border-top: 1px solid var(--color-divisor); }
.record-identifier { font: 12px/1.7 ui-monospace, monospace; overflow-wrap: anywhere; }
.editor-heading { margin-bottom: 28px; }
.editor-heading h2 { margin: 0 0 8px; font-size: 32px; letter-spacing: -0.5px; }
.editor-heading p { margin: 0; color: var(--color-secundario); line-height: 1.6; }
.editor-layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr); gap: 24px; align-items: start; }
.record-panel { min-width: 0; padding: 24px; border: 1px solid var(--color-divisor); border-radius: 12px; background: var(--color-superficie); }
.record-panel fieldset { margin: 0; }
.record-panel legend, .record-panel h3 { margin: 0 0 16px; padding: 0; font: 600 20px Georgia, serif; }
.record-panel label { margin-top: 0; margin-bottom: 8px; font-size: 13px; font-weight: 500; }
.record-panel input, .record-panel textarea, .record-panel select { padding: 12px; font-size: 16px; }
.record-panel textarea { min-height: 100px; resize: vertical; line-height: 1.6; }
.record-panel select + label, .record-panel #location { margin-top: 12px; }
.measurement-fields { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 16px; }
.editor-sidebar { display: grid; gap: 24px; min-width: 0; }
.editor-note p, .photo-editor p { color: var(--color-secundario); font-size: 13px; line-height: 1.6; }
.photo-editor .photos { gap: 8px; margin-bottom: 20px; }
.photo-editor .photos button { padding: 4px; }
.photo-editor .photos img { display: block; width: 64px; height: 64px; }
.editable-photo { display: grid; align-content: start; gap: 8px; width: 112px; margin: 0; }
.photo-editor .editable-photo > button img { width: 100%; height: 88px; object-fit: cover; }
.photo-position { color: var(--color-secundario); font-size: 12px; font-weight: 600; }
.photo-order-controls { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.photo-order-controls button { min-height: 44px; padding: 4px; border-color: var(--color-divisor); font-size: 24px; }
.editable-photo figcaption { color: var(--color-secundario); font-size: 12px; overflow-wrap: anywhere; }
.photo-editor .delete-photo { min-height: 44px; padding: 8px; border-color: var(--color-divisor); color: var(--color-error); font-size: 12px; }
.delete-photo-dialog { width: min(440px, calc(100% - 32px)); padding: 24px; border-radius: 12px; }
.delete-photo-dialog h3 { margin-top: 0; font-size: 24px; }
.delete-photo-dialog p { line-height: 1.6; }
.delete-photo-dialog .photo-note { color: var(--color-secundario); font-size: 13px; }
.photo-editor input[type="file"] { padding: 12px; border-style: dashed; font-size: 12px; }
.photo-editor input::file-selector-button { min-height: 36px; border: 0; border-radius: 4px; margin-right: 8px; padding: 8px; background: var(--color-footer); color: var(--color-texto); font: inherit; cursor: pointer; }
.photo-editor .photo-note { font-size: 12px; }
.state-actions { flex-direction: column; padding-top: 16px; border-top: 1px solid var(--color-divisor); }
.editor-footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--color-divisor); }
.editor-footer > p { color: var(--color-secundario); font-size: 12px; }
.editor-footer .actions { margin: 0; }
.primary-action { padding-inline: 24px; border-color: var(--color-acento); background: var(--color-acento); color: #fff; font-weight: 600; }
@media (min-width: 768px) {
  .wide-field { grid-column: 1 / -1; }
}
@media (max-width: 1000px) {
  .editor-layout { grid-template-columns: minmax(0, 1fr); }
  .editor-sidebar { grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: start; }
}
@media (max-width: 700px) {
  .piece-overview, .documentation-grid, .editor-sidebar { grid-template-columns: minmax(0, 1fr); }
  .piece-overview { gap: 28px; padding: 20px; }
  .piece-heading, .piece-documentation, .record-panel { padding: 20px; }
  .hero-photo img { height: 260px; }
  .no-photo { min-height: 220px; }
  .editor-heading h2 { font-size: 28px; }
  .editor-footer .actions { width: 100%; }
  .editor-footer .actions button { flex: 1; }
}
dialog {
  background: var(--color-control);
  color: var(--color-texto);
  border: 1px solid var(--color-borde);
  max-width: 90vw;
  max-height: 90vh;
}
dialog img {
  display: block;
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
}
dialog::backdrop {
  background: #000a;
}
@media (min-width: 768px) {
  .fields {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
