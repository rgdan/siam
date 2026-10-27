<script setup>
import { nextTick, ref } from "vue"
import { useI18n } from "vue-i18n"
import { enviar } from "../api.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t } = useI18n({ useScope: "global" })
const categorias = ["objeto_extraviado", "dano_infraestructura", "comportamiento_indebido", "emergencia_medica", "otro"]
const incidencia = ref({ description: "", category: "" })
const guardando = ref(false)
const mensaje = ref("")
const error = ref("")
const descripcion = ref(null)
const categoria = ref(null)
const confirmacion = ref(null)

function pedirConfirmacion() {
  if (guardando.value || confirmacion.value.open) return
  mensaje.value = ""
  error.value = ""
  if (Array.from(incidencia.value.description.trim()).length < 10) {
    error.value = "incidents.minimum"
    descripcion.value.focus()
    return
  }
  if (!incidencia.value.category) {
    error.value = "incidents.categoryRequired"
    categoria.value.focus()
    return
  }
  confirmacion.value.showModal()
}

async function guardar() {
  if (guardando.value || !confirmacion.value.open) return
  guardando.value = true
  confirmacion.value.close()
  try {
    const respuesta = await enviar("incidents/", {
      description: incidencia.value.description.trim(),
      category: incidencia.value.category,
    })
    if (respuesta.status === 401) emit("sesion-expirada")
    else if (respuesta.status === 403) emit("sin-acceso")
    else if (respuesta.status === 400) {
      const datos = await respuesta.json()
      error.value = datos.description ? "incidents.minimum" : "incidents.invalid"
    } else if (respuesta.status === 503) error.value = "incidents.saveError"
    else if (respuesta.status === 201) {
      incidencia.value = { description: "", category: "" }
      mensaje.value = "incidents.saved"
    } else throw new Error()
  } catch {
    error.value = "incidents.connectionError"
  } finally {
    guardando.value = false
    await nextTick()
    descripcion.value?.focus()
  }
}
</script>

<template>
  <section class="incidencias" aria-labelledby="titulo-incidencia">
    <h1 id="titulo-incidencia">{{ t("incidents.title") }}</h1>
    <p>{{ t("incidents.finalNotice") }}</p>
    <p role="status">{{ guardando ? t("incidents.saving") : mensaje ? t(mensaje) : "" }}</p>
    <p id="error-incidencia" role="alert" class="error">{{ error ? t(error) : "" }}</p>

    <form class="formulario" novalidate :aria-busy="guardando" @submit.prevent="pedirConfirmacion" @input="mensaje = ''">
      <fieldset :disabled="guardando">
        <label for="descripcion-incidencia">{{ t("incidents.description") }}</label>
        <textarea
          id="descripcion-incidencia" ref="descripcion" v-model="incidencia.description"
          name="description" rows="5" required minlength="10"
          aria-describedby="minimo-incidencia"
          :aria-invalid="error === 'incidents.minimum' || undefined"
          :aria-errormessage="error === 'incidents.minimum' ? 'error-incidencia' : undefined"
        ></textarea>
        <p id="minimo-incidencia" class="ayuda">{{ t("incidents.minimum") }}</p>
        <label for="categoria-incidencia">{{ t("incidents.category") }}</label>
        <select
          id="categoria-incidencia" ref="categoria" v-model="incidencia.category" name="category" required
          :aria-invalid="error === 'incidents.categoryRequired' || undefined"
          :aria-errormessage="error === 'incidents.categoryRequired' ? 'error-incidencia' : undefined"
        >
          <option disabled value="">{{ t("incidents.select") }}</option>
          <option v-for="opcion in categorias" :key="opcion" :value="opcion">{{ t(`incidents.categories.${opcion}`) }}</option>
        </select>
        <button type="submit">{{ t(error ? "incidents.retry" : "incidents.title") }}</button>
      </fieldset>
    </form>

    <dialog ref="confirmacion" aria-labelledby="titulo-confirmar-incidencia" aria-describedby="aviso-confirmar-incidencia">
      <h2 id="titulo-confirmar-incidencia">{{ t("incidents.confirmTitle") }}</h2>
      <p id="aviso-confirmar-incidencia">{{ t("incidents.finalNotice") }}</p>
      <dl>
        <dt>{{ t("incidents.category") }}</dt>
        <dd>{{ incidencia.category ? t(`incidents.categories.${incidencia.category}`) : "" }}</dd>
        <dt>{{ t("incidents.description") }}</dt>
        <dd class="descripcion">{{ incidencia.description.trim() }}</dd>
      </dl>
      <div class="acciones">
        <button type="button" autofocus @click="confirmacion.close()">{{ t("incidents.cancel") }}</button>
        <button type="button" class="confirmar" @click="guardar">{{ t("incidents.confirm") }}</button>
      </div>
    </dialog>
  </section>
</template>

<style scoped>
.incidencias { margin-block: 24px; overflow-wrap: anywhere; }
fieldset { display: grid; gap: 12px; margin: 0; padding: 0; border: 0; min-width: 0; }
textarea, select, button { min-height: 44px; padding: 10px 12px; border: 1px solid var(--color-borde); border-radius: 6px; font: inherit; }
textarea, select { width: 100%; min-width: 0; }
textarea { resize: vertical; }
.ayuda { margin: 0 0 8px; color: var(--color-secundario); }
button { background: var(--color-control); color: var(--color-texto); cursor: pointer; }
button[type="submit"], .confirmar { background: var(--color-acento); border-color: var(--color-acento); color: #fff; }
button:active { filter: brightness(0.9); }
button:disabled { cursor: wait; }
dialog { max-width: min(480px, calc(100% - 32px)); max-height: calc(100dvh - 32px); padding: 24px; background: var(--color-superficie); color: var(--color-texto); border: 1px solid var(--color-borde); overflow-wrap: anywhere; }
dt { font-weight: 600; }
dd { margin: 4px 0 16px; }
.descripcion { white-space: pre-wrap; }
.acciones { display: flex; flex-wrap: wrap; gap: 12px; }
.error { color: var(--color-error); }
@media (max-width: 480px) { .acciones > button { flex: 1 1 100%; } dialog { padding: 16px; } }
</style>
