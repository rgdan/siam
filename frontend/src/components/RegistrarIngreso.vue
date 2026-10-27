<script setup>
import { nextTick, ref } from "vue"
import { useI18n } from "vue-i18n"
import { enviar } from "../api.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t } = useI18n({ useScope: "global" })
const entrada = ref({ age_group: "", nationality: "", sex: "" })
const guardando = ref(false)
const mensaje = ref("")
const error = ref("")
const edad = ref(null)
const confirmacion = ref(null)

function pedirConfirmacion() {
  if (guardando.value || confirmacion.value.open) return
  mensaje.value = ""
  error.value = ""
  confirmacion.value.showModal()
}

async function guardar() {
  if (guardando.value || !confirmacion.value.open) return
  guardando.value = true
  confirmacion.value.close()
  try {
    const respuesta = await enviar("visitor-entries/", { ...entrada.value })
    if (respuesta.status === 401) emit("sesion-expirada")
    else if (respuesta.status === 403) emit("sin-acceso")
    else if (respuesta.status === 400) error.value = "visitors.invalid"
    else if (respuesta.status === 503) error.value = "visitors.saveError"
    else if (respuesta.status === 201) {
      entrada.value = { age_group: "", nationality: "", sex: "" }
      mensaje.value = "visitors.saved"
    } else throw new Error()
  } catch {
    error.value = "visitors.connectionError"
  } finally {
    guardando.value = false
    await nextTick()
    edad.value?.focus()
  }
}
</script>

<template>
  <section class="ingresos" aria-labelledby="titulo-ingreso">
    <h1 id="titulo-ingreso">{{ t("visitors.title") }}</h1>
    <p role="status">{{ guardando ? t("visitors.saving") : mensaje ? t(mensaje) : "" }}</p>
    <p role="alert" class="error">{{ error ? t(error) : "" }}</p>

    <form class="formulario" :aria-busy="guardando" @submit.prevent="pedirConfirmacion" @change="mensaje = ''">
      <fieldset :disabled="guardando">
        <label for="edad-visitante">{{ t("visitors.age") }}</label>
        <select id="edad-visitante" ref="edad" v-model="entrada.age_group" name="age_group" required>
          <option disabled value="">{{ t("visitors.select") }}</option>
          <option value="mayor">{{ t("visitors.options.mayor") }}</option>
          <option value="menor">{{ t("visitors.options.menor") }}</option>
        </select>
        <label for="nacionalidad-visitante">{{ t("visitors.nationality") }}</label>
        <select id="nacionalidad-visitante" v-model="entrada.nationality" name="nationality" required>
          <option disabled value="">{{ t("visitors.select") }}</option>
          <option value="nacional">{{ t("visitors.options.nacional") }}</option>
          <option value="extranjero">{{ t("visitors.options.extranjero") }}</option>
        </select>
        <label for="sexo-visitante">{{ t("visitors.sex") }}</label>
        <select id="sexo-visitante" v-model="entrada.sex" name="sex" required>
          <option disabled value="">{{ t("visitors.select") }}</option>
          <option value="masculino">{{ t("visitors.options.masculino") }}</option>
          <option value="femenino">{{ t("visitors.options.femenino") }}</option>
        </select>
        <button type="submit">{{ t(error ? "visitors.retry" : "visitors.title") }}</button>
      </fieldset>
    </form>

    <dialog ref="confirmacion" aria-labelledby="titulo-confirmar-ingreso" aria-describedby="descripcion-confirmar-ingreso">
      <h2 id="titulo-confirmar-ingreso">{{ t("visitors.confirmTitle") }}</h2>
      <p id="descripcion-confirmar-ingreso">{{ t("visitors.confirmDescription") }}</p>
      <dl>
        <dt>{{ t("visitors.age") }}</dt>
        <dd>{{ entrada.age_group ? t(`visitors.options.${entrada.age_group}`) : "" }}</dd>
        <dt>{{ t("visitors.nationality") }}</dt>
        <dd>{{ entrada.nationality ? t(`visitors.options.${entrada.nationality}`) : "" }}</dd>
        <dt>{{ t("visitors.sex") }}</dt>
        <dd>{{ entrada.sex ? t(`visitors.options.${entrada.sex}`) : "" }}</dd>
      </dl>
      <div class="acciones">
        <button type="button" autofocus @click="confirmacion.close()">{{ t("visitors.cancel") }}</button>
        <button type="button" class="confirmar" @click="guardar">{{ t("visitors.confirm") }}</button>
      </div>
    </dialog>
  </section>
</template>

<style scoped>
.ingresos { margin-block: 24px; overflow-wrap: anywhere; }
fieldset { display: grid; gap: 12px; margin: 0; padding: 0; border: 0; min-width: 0; }
select, button { min-height: 44px; padding: 10px 12px; border: 1px solid var(--color-borde); border-radius: 6px; font: inherit; }
select { width: 100%; min-width: 0; }
button { background: var(--color-control); color: var(--color-texto); cursor: pointer; }
button[type="submit"], .confirmar { background: var(--color-acento); border-color: var(--color-acento); color: #fff; }
button:active { filter: brightness(0.9); }
button:disabled { cursor: wait; }
dialog { max-width: min(480px, calc(100% - 32px)); padding: 24px; background: var(--color-superficie); color: var(--color-texto); border: 1px solid var(--color-borde); overflow-wrap: anywhere; }
dt { font-weight: 600; }
dd { margin: 4px 0 16px; }
.acciones { display: flex; flex-wrap: wrap; gap: 12px; }
.error { color: var(--color-error); }
@media (max-width: 480px) { .acciones > button { flex: 1 1 100%; } dialog { padding: 16px; } }
</style>
