<script setup>
import { ref, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar, enviar } from "../api.js"
import messages from "./collectionMessages.js"
const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t } = useI18n({ messages, useScope: "local" })
const fields = [
  "object_type",
  "materials_techniques",
  "inscriptions_marks",
  "distinguishing_features",
  "title",
  "subject",
  "date_period",
  "author_maker",
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
const stateForm = ref({}),
  photoResults = ref([]),
  enlarged = ref(null),
  dialog = ref(null)
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
  stateForm.value = {
    state: selected.value.state,
    location: selected.value.location,
  }
  mode.value = "detail"
  errors.value = {}
}
async function open(id) {
  busy.value = true
  failure.value = false
  notice.value = ""
  photoResults.value = []
  try {
    await detail(id)
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
        [...fields, "measurement_value", "measurement_unit"].map((f) => [
          f,
          selected.value[f],
        ]),
      )
  if (create) form.value.measurement_unit = "cm"
}
function validate() {
  errors.value = {}
  for (const field of fields)
    if (!String(form.value[field] || "").trim())
      errors.value[field] = "required"
  const value = String(form.value.measurement_value)
  if (!/^\d+(\.\d{1,4})?$/.test(value) || Number(value) <= 0)
    errors.value.measurement_value = "positive"
  return !Object.keys(errors.value).length
}
async function save(stateOnly = false) {
  if (busy.value || (!stateOnly && !validate())) return
  errors.value = {}
  failure.value = false
  busy.value = true
  notice.value = ""
  try {
    const creating = mode.value === "new"
    const data = stateOnly ? { ...stateForm.value } : { ...form.value }
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
  return t(["required", "positive"].includes(value) ? value : "invalid")
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
    await detail(selected.value.id)
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
onMounted(load)
</script>
<template>
  <section class="collection" :aria-busy="busy">
    <h2>{{ t("title") }}</h2>
    <p v-if="busy" role="status">{{ t("loading") }}</p>
    <p v-if="notice" role="status">{{ t(notice) }}</p>
    <p v-if="failure" role="alert" class="error">{{ t("error") }}</p>
    <template v-if="mode === 'list'">
      <div class="actions">
        <button :disabled="busy" @click="edit(true)">{{ t("new") }}</button
        ><button :disabled="busy" @click="load">{{ t("refresh") }}</button>
      </div>
      <label for="state-filter">{{ t("state") }}</label
      ><select
        id="state-filter"
        v-model="filter"
        :disabled="busy"
        @change="load"
      >
        <option value="">{{ t("all") }}</option>
        <option value="stored">{{ t("stored") }}</option>
        <option value="displayed">{{ t("displayed") }}</option>
      </select>
      <p v-if="!busy && !pieces.length">{{ t("empty") }}</p>
      <ul class="pieces">
        <li v-for="piece in pieces" :key="piece.id">
          <button :disabled="busy" @click="open(piece.id)">
            {{ piece.title }}</button
          ><small>{{ piece.identifier }}</small>
          <p>
            {{ t(piece.state)
            }}<span v-if="piece.state === 'displayed'">
              / {{ piece.location }}</span
            >
          </p>
        </li>
      </ul>
    </template>
    <template v-else-if="mode === 'new' || mode === 'edit'">
      <h3>{{ t(mode === "new" ? "new" : "edit") }}</h3>
      <p v-if="mode === 'edit'">
        {{ t("identifier") }}: {{ selected.identifier }}
      </p>
      <form novalidate @submit.prevent="save()">
        <fieldset :disabled="busy" class="fields">
          <div v-for="field in fields" :key="field">
            <label :for="field">{{ label(field) }} *</label
            ><textarea
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
          <div>
            <label for="measurement">{{ t("measurements") }} *</label
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
            <label for="unit">{{ t("measurement_unit") }}</label
            ><select id="unit" v-model="form.measurement_unit">
              <option v-for="unit in ['mm', 'cm', 'm', 'g', 'kg']" :key="unit">
                {{ unit }}
              </option>
            </select>
          </div>
        </fieldset>
        <div class="actions">
          <button :disabled="busy">{{ t("save") }}</button
          ><button
            type="button"
            :disabled="busy"
            @click="cancelEdit"
          >
            {{ t("cancel") }}
          </button>
        </div>
      </form>
    </template>
    <template v-else-if="selected">
      <button
        :disabled="busy"
        @click="backToCollection"
      >
        {{ t("back") }}
      </button>
      <h3>{{ selected.title }}</h3>
      <p>{{ t("identifier") }}: {{ selected.identifier }}</p>
      <dl>
        <template v-for="field in fields" :key="field"
          ><dt>{{ label(field) }}</dt>
          <dd>{{ selected[field] }}</dd></template
        >
        <dt>{{ t("measurements") }}</dt>
        <dd>
          {{ selected.measurement_value }} {{ selected.measurement_unit }}
        </dd>
        <dt>{{ t("state") }}</dt>
        <dd>{{ t(selected.state) }}</dd>
        <template v-if="selected.state === 'displayed'"
          ><dt>{{ t("location") }}</dt>
          <dd>{{ selected.location }}</dd></template
        >
      </dl>
      <button v-if="!selected.decommissioned" :disabled="busy" @click="edit()">
        {{ t("edit") }}
      </button>
      <form
        v-if="!selected.decommissioned"
        novalidate
        @submit.prevent="save(true)"
      >
        <fieldset :disabled="busy">
          <label for="piece-state">{{ t("state") }}</label
          ><select id="piece-state" v-model="stateForm.state">
            <option value="stored">{{ t("stored") }}</option>
            <option value="displayed">{{ t("displayed") }}</option></select
          ><template v-if="stateForm.state === 'displayed'"
            ><label for="location">{{ t("location") }} *</label
            ><input
              id="location"
              v-model="stateForm.location"
              maxlength="200"
              required
              :aria-invalid="!!errors.location"
              aria-describedby="location-error"
            />
            <p v-if="errors.location" id="location-error" class="error">
              {{ fieldError("location") }}
            </p></template
          ><button>{{ t("save") }}</button>
        </fieldset>
      </form>
      <h3>{{ t("photos") }}</h3>
      <p v-if="!selected.photos.length">{{ t("noPhotos") }}</p>
      <div class="photos">
        <button
          v-for="photo in selected.photos"
          :key="photo.id"
          @click="showPhoto(photo)"
        >
          <img :src="photo.data" :alt="photo.name" />
        </button>
      </div>
      <label for="photos">{{ t("addPhotos") }}</label>
      <p id="photo-help">{{ t("photoHelp") }}</p>
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
    </template>
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
  cursor: wait;
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
.pieces {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 16px;
}
.pieces li {
  padding: 16px;
  border: 1px solid var(--color-borde);
  border-radius: 8px;
}
.pieces small {
  display: block;
  margin-top: 8px;
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
  .pieces {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
