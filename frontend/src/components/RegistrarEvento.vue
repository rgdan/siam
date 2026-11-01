
<script setup>
import { reactive, ref } from "vue"
import { useI18n } from "vue-i18n"
import { enviar } from "../api.js"

const emit = defineEmits(["sesion-expirada", "sin-acceso"])
const { t } = useI18n({ useScope: "global" })

const formulario = reactive({
  fecha: "",
  descripcion: "",
  ubicacion: "",
  tipo: "publico",
  asistentes_esperados: 1,
})

const guardando = ref(false)
const guardado = ref(false)
const error = ref("")
const erroresCampos = ref({})

function limpiarFormulario() {
  formulario.fecha = ""
  formulario.descripcion = ""
  formulario.ubicacion = ""
  formulario.tipo = "publico"
  formulario.asistentes_esperados = 1
}

function mensajeCampo(campo) {
  const mensaje = erroresCampos.value[campo]
  return mensaje?.clave ? t(mensaje.clave) : mensaje?.texto || ""
}

function validar() {
  const errores = {}

  const fecha = new Date(formulario.fecha).getTime()

  if (!formulario.fecha || !Number.isFinite(fecha) || fecha <= Date.now()) {
    errores.fecha = { clave: "events.futureDate" }
  }

  if (
    !formulario.descripcion.trim() ||
    formulario.descripcion.trim().length > 500
  ) {
    errores.descripcion = { clave: "events.descriptionRule" }
  }

  if (!formulario.ubicacion.trim()) {
    errores.ubicacion = { clave: "events.locationRequired" }
  }

  if (!["publico", "privado"].includes(formulario.tipo)) {
    errores.tipo = { clave: "events.typeRequired" }
  }

  if (
    !Number.isInteger(Number(formulario.asistentes_esperados)) ||
    Number(formulario.asistentes_esperados) < 1
  ) {
    errores.asistentes_esperados = { clave: "events.attendeesRule" }
  }

  erroresCampos.value = errores
  return Object.keys(errores).length === 0
}

async function registrarEvento() {
  if (guardando.value) return

  guardado.value = false
  error.value = ""

  if (!validar()) return

  guardando.value = true

  try {
    const respuesta = await enviar("events/", {
      fecha: new Date(formulario.fecha).toISOString(),
      descripcion: formulario.descripcion.trim(),
      ubicacion: formulario.ubicacion.trim(),
      tipo: formulario.tipo,
      asistentes_esperados: Number(formulario.asistentes_esperados),
    })

    if (respuesta.status === 401) {
      emit("sesion-expirada")
      return
    }

    if (respuesta.status === 403) {
      emit("sin-acceso")
      return
    }

    if (respuesta.status === 400) {
      const datos = await respuesta.json()

      erroresCampos.value = Object.fromEntries(
        Object.entries(datos)
          .filter(([, valor]) => Array.isArray(valor))
          .map(([campo, mensajes]) => [
            campo,
            { texto: mensajes.join(" ") },
          ])
      )

      error.value = "events.invalid"
      return
    }

    if (!respuesta.ok) throw new Error()

    limpiarFormulario()
    erroresCampos.value = {}
    guardado.value = true
  } catch {
    error.value = "events.connectionError"
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <section class="registro-evento">
    <h2>{{ t("events.registerTitle") }}</h2>
    <p>{{ t("events.instructions") }}</p>

    <form :aria-busy="guardando" @submit.prevent="registrarEvento">
      <div class="campo">
        <label for="evento-fecha">{{ t("events.dateTime") }}</label>
        <input
          id="evento-fecha"
          v-model="formulario.fecha"
          type="datetime-local"
          required
          :disabled="guardando"
          :aria-invalid="!!erroresCampos.fecha"
        />
        <p v-if="erroresCampos.fecha" role="alert" class="mensaje-error">
          {{ mensajeCampo("fecha") }}
        </p>
      </div>

      <div class="campo">
        <label for="evento-descripcion">{{ t("events.description") }}</label>
        <textarea
          id="evento-descripcion"
          v-model="formulario.descripcion"
          maxlength="500"
          rows="4"
          required
          :disabled="guardando"
          :aria-invalid="!!erroresCampos.descripcion"
        />
        <p class="ayuda">{{ formulario.descripcion.length }}/500</p>
        <p v-if="erroresCampos.descripcion" role="alert" class="mensaje-error">
          {{ mensajeCampo("descripcion") }}
        </p>
      </div>

      <div class="campo">
        <label for="evento-ubicacion">{{ t("events.location") }}</label>
        <input
          id="evento-ubicacion"
          v-model="formulario.ubicacion"
          type="text"
          maxlength="200"
          required
          :disabled="guardando"
          :aria-invalid="!!erroresCampos.ubicacion"
        />
        <p v-if="erroresCampos.ubicacion" role="alert" class="mensaje-error">
          {{ mensajeCampo("ubicacion") }}
        </p>
      </div>

      <div class="campo">
        <label for="evento-tipo">{{ t("events.type") }}</label>
        <select
          id="evento-tipo"
          v-model="formulario.tipo"
          required
          :disabled="guardando"
        >
          <option value="publico">{{ t("events.public") }}</option>
          <option value="privado">{{ t("events.private") }}</option>
        </select>
        <p v-if="erroresCampos.tipo" role="alert" class="mensaje-error">
          {{ mensajeCampo("tipo") }}
        </p>
      </div>

      <div class="campo">
        <label for="evento-asistentes">{{ t("events.expectedAttendees") }}</label>
        <input
          id="evento-asistentes"
          v-model.number="formulario.asistentes_esperados"
          type="number"
          min="1"
          step="1"
          required
          :disabled="guardando"
          :aria-invalid="!!erroresCampos.asistentes_esperados"
        />
        <p v-if="erroresCampos.asistentes_esperados" role="alert" class="mensaje-error">
          {{ mensajeCampo("asistentes_esperados") }}
        </p>
      </div>

      <button type="submit" :disabled="guardando">
        {{ guardando ? t("events.saving") : t("events.save") }}
      </button>
    </form>

    <p v-if="guardado" role="status" class="mensaje-exito">
      {{ t("events.saved") }}
    </p>

    <p v-if="error" role="alert" class="mensaje-error">
      {{ t(error) }}
    </p>
  </section>
</template>

<style scoped>
.registro-evento {
  width: 100%;
  max-width: 680px;
  min-width: 0;
  margin: 0 auto;
  color: var(--color-texto);
}

form, .campo {
  display: grid;
  gap: 10px;
}

form {
  gap: 20px;
  margin-top: 24px;
}

label {
  font-weight: 600;
}

input, textarea, select, button {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  font: inherit;
}

input, textarea, select {
  background: var(--color-control);
  color: var(--color-texto);
}

textarea {
  resize: vertical;
}

button {
  background: var(--color-header);
  color: #ffffff;
  cursor: pointer;
  font-weight: 600;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.ayuda {
  margin: 0;
  font-size: 13px;
}

.mensaje-error {
  color: var(--color-error);
}

.mensaje-exito {
  font-weight: 600;
}

@media (max-width: 400px) {
  .registro-evento {
    padding: 0;
  }
}
</style>
