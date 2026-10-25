<script setup>
import { nextTick, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { enviar, solicitar } from "../api.js"

const props = defineProps({ usuarioActual: { type: Object, required: true } })
const emit = defineEmits(["sesion-expirada", "sin-acceso", "cuenta-actualizada"])
const { t } = useI18n({ useScope: "global" })
const roles = ["guarda", "coordinador", "museologo", "administrador_general", "administrador_sistema"]
const cuentas = ref([])
const cargando = ref(true)
const guardando = ref(false)
const error = ref("")
const mensaje = ref("")
const formulario = ref(null)
const nombre = ref(null)
const confirmacion = ref(null)

// Un rechazo elimina la vista interna; los errores de validación se muestran sin perder el formulario.
async function leer(respuesta) {
  const datos = await respuesta.json()
  if (respuesta.status === 401) emit("sesion-expirada")
  else if (respuesta.status === 403) emit("sin-acceso")
  else if (respuesta.ok) return datos
  else error.value = Object.values(datos).flat().join(" ")
  throw new Error()
}

// Actualiza la lista desde Django, sin conservar contraseñas en las cuentas mostradas.
async function cargar() {
  cargando.value = true
  error.value = ""
  try {
    cuentas.value = await leer(await solicitar("users/"))
  } catch {
    error.value ||= t("users.loadError")
  } finally {
    cargando.value = false
  }
}

// Copia únicamente campos editables y deja siempre vacía la contraseña de restablecimiento.
async function seleccionar(cuenta = null) {
  formulario.value = {
    id: cuenta?.id ?? null,
    full_name: cuenta?.full_name ?? "",
    email: cuenta?.email ?? "",
    role: cuenta?.role ?? "guarda",
    is_active: cuenta?.is_active ?? true,
    password: "",
  }
  mensaje.value = ""
  error.value = ""
  await nextTick()
  nombre.value?.focus()
}

// La contraseña vacía significa conservar la actual, nunca reemplazarla por una vacía.
async function guardar() {
  if (guardando.value) return
  guardando.value = true
  error.value = ""
  mensaje.value = ""
  const { id, ...datos } = formulario.value
  if (id && !datos.password) delete datos.password
  try {
    await leer(await enviar(id ? `users/${id}/` : "users/", datos, id ? "PATCH" : "POST"))
    formulario.value = null
    mensaje.value = t("users.saved")
    await cargar()
    if (id === props.usuarioActual.id) emit("cuenta-actualizada")
  } catch {
    error.value ||= t("users.saveError")
  } finally {
    if (formulario.value) formulario.value.password = ""
    guardando.value = false
  }
}

// El diálogo nativo admite teclado y Escape, y exige confirmar antes de enviar DELETE.
function pedirEliminacion() {
  confirmacion.value.showModal()
}

// Django decide si elimina la cuenta o la desactiva para conservar sus registros.
async function eliminar() {
  if (guardando.value) return
  guardando.value = true
  error.value = ""
  mensaje.value = ""
  try {
    const resultado = await leer(await enviar(`users/${formulario.value.id}/`, { confirm: true }, "DELETE"))
    formulario.value = null
    mensaje.value = t(resultado.action === "deactivated" ? "users.deactivated" : "users.deleted")
    await cargar()
  } catch {
    error.value ||= t("users.saveError")
  } finally {
    confirmacion.value?.close()
    guardando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <section aria-labelledby="titulo-usuarios" class="usuarios">
    <h2 id="titulo-usuarios">{{ t("users.title") }}</h2>
    <p class="borrador">{{ t("users.draft") }}</p>
    <div class="acciones">
      <button type="button" :disabled="guardando || cargando" @click="seleccionar()">{{ t("users.create") }}</button>
      <button type="button" :disabled="guardando || cargando" @click="cargar">{{ t("users.refresh") }}</button>
    </div>
    <p v-if="cargando" role="status">{{ t("users.loading") }}</p>
    <p v-else-if="!cuentas.length && !error">{{ t("users.empty") }}</p>
    <ul v-else class="cuentas" :aria-label="t('users.title')">
      <li v-for="cuenta in cuentas" :key="cuenta.id">
        <span>
          <strong>{{ cuenta.full_name }}</strong><br />
          {{ cuenta.email }}<br />
          {{ t(`roles.${cuenta.role}`) }} · {{ t(cuenta.is_active ? "users.active" : "users.inactive") }}
        </span>
        <button type="button" :disabled="guardando || cargando" :aria-label="t('users.editAccount', { name: cuenta.full_name })" @click="seleccionar(cuenta)">{{ t("users.edit") }}</button>
      </li>
    </ul>

    <form v-if="formulario" class="formulario" :aria-busy="guardando" @submit.prevent="guardar">
      <h3>{{ t(formulario.id ? "users.edit" : "users.create") }}</h3>
      <fieldset :disabled="guardando">
        <label for="nombre-usuario">{{ t("users.fullName") }}</label>
        <input id="nombre-usuario" ref="nombre" v-model.trim="formulario.full_name" autocomplete="name" maxlength="200" required />
        <label for="correo-usuario">{{ t("auth.email") }}</label>
        <input id="correo-usuario" v-model.trim="formulario.email" type="email" autocomplete="off" maxlength="254" required />
        <label for="rol-usuario">{{ t("users.role") }}</label>
        <select id="rol-usuario" v-model="formulario.role">
          <option v-for="rol in roles" :key="rol" :value="rol">{{ t(`roles.${rol}`) }}</option>
        </select>
        <template v-if="formulario.id">
          <label for="estado-usuario">{{ t("users.status") }}</label>
          <select id="estado-usuario" v-model="formulario.is_active" :disabled="formulario.id === usuarioActual.id">
            <option :value="true">{{ t("users.active") }}</option>
            <option :value="false">{{ t("users.inactive") }}</option>
          </select>
        </template>
        <label for="clave-usuario">{{ t(formulario.id ? "users.resetPassword" : "auth.password") }}</label>
        <input id="clave-usuario" v-model="formulario.password" type="password" autocomplete="new-password" minlength="8" :required="!formulario.id" aria-describedby="ayuda-clave" />
        <p id="ayuda-clave">{{ t(formulario.id ? "users.passwordOptional" : "users.passwordRule") }}</p>
        <div class="acciones">
          <button type="submit">{{ t("users.save") }}</button>
          <button type="button" @click="formulario = null">{{ t("users.cancel") }}</button>
          <button v-if="formulario.id && formulario.id !== usuarioActual.id" type="button" @click="pedirEliminacion">{{ t("users.delete") }}</button>
        </div>
      </fieldset>
    </form>
    <p role="status">{{ guardando ? t("common.processing") : mensaje }}</p>
    <p role="alert" class="error">{{ error }}</p>

    <dialog ref="confirmacion" aria-labelledby="titulo-eliminar" :aria-busy="guardando" @cancel="guardando && $event.preventDefault()">
      <h3 id="titulo-eliminar">{{ t("users.confirmDelete") }}</h3>
      <p>{{ formulario?.full_name }}</p>
      <p>{{ t("users.deleteWarning") }}</p>
      <div class="acciones">
        <button type="button" :disabled="guardando" @click="confirmacion.close()" autofocus>{{ t("users.cancel") }}</button>
        <button type="button" :disabled="guardando" @click="eliminar">{{ t("users.delete") }}</button>
      </div>
    </dialog>
  </section>
</template>

<style scoped>
.usuarios { margin-block: 24px; overflow-wrap: anywhere; }
.acciones { display: flex; flex-wrap: wrap; gap: 12px; }
.cuentas { list-style: none; padding: 0; }
.cuentas li { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; padding-block: 16px; border-bottom: 1px solid var(--color-borde); }
.cuentas span { min-width: 0; flex: 1 1 240px; }
fieldset { display: grid; gap: 12px; margin: 0; padding: 0; border: 0; min-width: 0; }
input, select, button { min-height: 44px; padding: 10px 12px; border: 1px solid var(--color-borde); border-radius: 6px; font: inherit; }
input, select { width: 100%; min-width: 0; }
button { background: var(--color-control); color: var(--color-texto); cursor: pointer; }
button[type="submit"] { background: var(--color-header); color: #fff; }
button:disabled { cursor: wait; }
dialog { max-width: min(480px, calc(100% - 32px)); padding: 24px; background: var(--color-superficie); color: var(--color-texto); border: 1px solid var(--color-borde); overflow-wrap: anywhere; }
.error { color: var(--color-error); }
@media (max-width: 480px) { .acciones > button { flex: 1 1 100%; } .cuentas li > button { width: 100%; } }
</style>
