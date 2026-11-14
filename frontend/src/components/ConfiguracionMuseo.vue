<script setup>
import { onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar, enviar } from "../api.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t } = useI18n({ useScope: "global" })
const valores = ref(null)
const cargando = ref(true)
const guardando = ref(false)
const error = ref("")
const mensaje = ref("")
const errores = ref({})
const dias = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
const ordenDias = [1, 2, 3, 4, 5, 6, 0]
const campos = ["museum_name", "address", "location"]

function comprobarAcceso(respuesta) {
  if (respuesta.status === 401) emit("sesion-expirada")
  else if (respuesta.status === 403) emit("sin-acceso")
  else return true
  valores.value = null
  return false
}

async function cargar() {
  cargando.value = true
  error.value = ""
  try {
    const respuesta = await solicitar("configuration/")
    if (!comprobarAcceso(respuesta)) return
    if (!respuesta.ok) throw new Error()
    const datos = await respuesta.json()
    valores.value = datos.values
  } catch {
    error.value = "configuration.loadError"
  } finally {
    cargando.value = false
  }
}

function cambiarCierre(dia, cerrado) {
  valores.value.opening_hours[dia] = cerrado
    ? { opens: null, closes: null }
    : { opens: "09:00", closes: "17:00" }
}

async function guardar() {
  if (guardando.value) return
  guardando.value = true
  error.value = ""
  mensaje.value = ""
  errores.value = {}
  try {
    const respuesta = await enviar("configuration/", valores.value, "PATCH")
    if (!comprobarAcceso(respuesta)) return
    if (respuesta.status === 400) {
      errores.value = await respuesta.json()
      error.value = "configuration.invalid"
    } else {
      if (!respuesta.ok) throw new Error()
      valores.value = (await respuesta.json()).values
      mensaje.value = "configuration.saved"
    }
  } catch {
    error.value = "configuration.saveError"
  } finally {
    guardando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <section class="configuracion" aria-labelledby="titulo-configuracion">
    <h1 id="titulo-configuracion">{{ t("configuration.title") }}</h1>
    <p>{{ t("configuration.description") }}</p>
    <p role="status">{{ cargando ? t("configuration.loading") : guardando ? t("configuration.saving") : mensaje ? t(mensaje) : "" }}</p>
    <p v-if="error" role="alert" class="error">{{ t(error) }}</p>
    <button v-if="!cargando && !valores" type="button" @click="cargar">{{ t("configuration.retry") }}</button>

    <form v-if="valores" :aria-busy="guardando" @submit.prevent="guardar" @input="mensaje = ''">
      <fieldset :disabled="guardando">
        <div v-for="campo in campos" :key="campo" class="campo">
          <label :for="`config-${campo}`">{{ t(`configuration.${campo}`) }}</label>
          <input
            :id="`config-${campo}`" v-model="valores[campo]" :name="campo" required
            :maxlength="campo === 'museum_name' ? 200 : 500"
            :aria-invalid="errores[campo] ? true : undefined"
            :aria-describedby="errores[campo] ? `error-${campo}` : undefined"
          >
          <p v-if="errores[campo]" :id="`error-${campo}`" class="error">{{ t("configuration.invalidField") }}</p>
        </div>

        <div class="campo">
          <label for="config-default_language">{{ t("configuration.default_language") }}</label>
          <select id="config-default_language" v-model="valores.default_language" name="default_language" aria-describedby="idioma-configuracion">
            <option value="es">Español</option>
            <option value="en">English</option>
          </select>
          <p id="idioma-configuracion" class="ayuda">{{ t("configuration.languageHint") }}</p>
        </div>

        <fieldset class="horarios">
          <legend>{{ t("configuration.opening_hours") }}</legend>
          <fieldset v-for="dia in ordenDias" :key="dia" class="dia">
            <legend>{{ t(`museum.days.${dias[dia]}`) }}</legend>
            <label class="cerrado">
              <input type="checkbox" :checked="valores.opening_hours[dia].opens === null" @change="cambiarCierre(dia, $event.target.checked)">
              {{ t("museum.closed") }}
            </label>
            <template v-if="valores.opening_hours[dia].opens !== null">
              <div class="campo">
                <label :for="`apertura-${dia}`">{{ t("museum.opening") }}</label>
                <input :id="`apertura-${dia}`" v-model="valores.opening_hours[dia].opens" type="time" required :aria-invalid="errores.opening_hours?.[dia] ? true : undefined" :aria-describedby="errores.opening_hours?.[dia] ? `error-dia-${dia}` : undefined">
              </div>
              <div class="campo">
                <label :for="`cierre-${dia}`">{{ t("museum.closing") }}</label>
                <input :id="`cierre-${dia}`" v-model="valores.opening_hours[dia].closes" type="time" required :aria-invalid="errores.opening_hours?.[dia] ? true : undefined" :aria-describedby="errores.opening_hours?.[dia] ? `error-dia-${dia}` : undefined">
              </div>
            </template>
            <p v-if="errores.opening_hours?.[dia]" :id="`error-dia-${dia}`" class="error">{{ t("configuration.invalidHours") }}</p>
          </fieldset>
        </fieldset>
        <button type="submit">{{ t("configuration.save") }}</button>
      </fieldset>
    </form>
  </section>
</template>

<style scoped>
.configuracion { overflow-wrap: anywhere; }
h1 { margin-bottom: 8px; }
fieldset { min-width: 0; margin: 0; padding: 0; border: 0; }
form > fieldset { display: grid; gap: 24px; }
.campo { display: grid; gap: 8px; min-width: 0; }
input, select, button { min-height: 44px; padding: 10px 12px; border: 1px solid var(--color-borde); border-radius: 6px; font: inherit; color: var(--color-texto); background: var(--color-control); }
input, select { width: 100%; min-width: 0; box-sizing: border-box; }
button { cursor: pointer; }
button[type="submit"] { justify-self: start; color: #fff; background: var(--color-acento); border-color: var(--color-acento); }
button:disabled { cursor: wait; }
input[aria-invalid="true"] { border-color: var(--color-error); }
.ayuda { color: var(--color-secundario); font-size: 14px; }
.error { color: var(--color-error); }
.campo p { margin: 0; }
.horarios > legend { margin-bottom: 16px; font-weight: 600; }
.dia { display: grid; grid-template-columns: minmax(100px, 1fr) repeat(2, minmax(0, 1fr)); gap: 12px; padding-block: 16px; border-top: 1px solid var(--color-divisor); }
.dia legend { padding-top: 16px; }
.cerrado { display: flex; align-items: center; gap: 8px; min-height: 44px; }
.cerrado input { width: 20px; min-height: 20px; margin: 0; }
.dia > .error { grid-column: 1 / -1; margin: 0; }
@media (max-width: 560px) {
  .dia { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cerrado { grid-column: 1 / -1; }
}
</style>
