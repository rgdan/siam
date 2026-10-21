
<script setup>
import { onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import AppLayout from "./components/AppLayout.vue"

// Traducciones de SIAM.
const { t } = useI18n({ useScope: "global" })

// Estado de autenticación.
const usuario = ref(null)
const correo = ref("")
const contrasena = ref("")
const comprobando = ref(true)
const enviando = ref(false)

// Guardamos la clave del error para que cambie con el idioma.
const error = ref("")

// Todas las solicitudes usan la URL configurada,
// incluyen cookies y esperan hasta 5 segundos.
function solicitar(ruta, opciones = {}) {
  return fetch(`${import.meta.env.VITE_API_BASE_URL}${ruta}`, {
    ...opciones,
    credentials: "include",
    signal: AbortSignal.timeout(5000),
  })
}

// Obtiene un token CSRF vigente antes de cada POST.
async function enviar(ruta, datos = {}) {
  const respuesta = await solicitar("auth/csrf/")

  if (!respuesta.ok) throw new Error()

  const { csrfToken } = await respuesta.json()

  if (typeof csrfToken !== "string") throw new Error()

  return solicitar(ruta, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(datos),
  })
}

// Django confirma la identidad del usuario.
async function cargarSesion() {
  const respuesta = await solicitar("auth/me/")

  if (respuesta.status === 401) {
    usuario.value = null
  } else {
    if (!respuesta.ok) throw new Error()

    const datos = await respuesta.json()

    if (!datos.id || typeof datos.full_name !== "string") {
      throw new Error()
    }

    usuario.value = datos
  }

  window.history.replaceState(
    null,
    "",
    usuario.value ? "/interno" : "/login"
  )
}

// Inicia sesión utilizando Django.
async function ingresar() {
  if (enviando.value) return

  enviando.value = true
  error.value = ""

  try {
    const respuesta = await enviar("auth/login/", {
      email: correo.value,
      password: contrasena.value,
    })

    if (respuesta.status === 401) {
      error.value = "auth.invalidCredentials"
      return
    }

    if (!respuesta.ok) throw new Error()

    await cargarSesion()

    if (!usuario.value) {
      error.value = "auth.sessionUnavailable"
    }
  } catch {
    error.value = "auth.loginError"
  } finally {
    contrasena.value = ""
    enviando.value = false
  }
}

// Cierra la sesión del usuario.
async function cerrarSesion() {
  if (enviando.value) return

  enviando.value = true
  error.value = ""

  try {
    const respuesta = await enviar("auth/logout/")

    if (!respuesta.ok && respuesta.status !== 401) {
      throw new Error()
    }

    usuario.value = null
    correo.value = ""

    window.history.replaceState(null, "", "/login")
  } catch {
    error.value = "auth.logoutError"
  } finally {
    enviando.value = false
  }
}

// Comprueba la sesión al abrir o recargar la página.
onMounted(async () => {
  try {
    await cargarSesion()
  } catch {
    window.history.replaceState(null, "", "/login")
    error.value = "auth.sessionError"
  } finally {
    comprobando.value = false
  }
})
</script>

<template>
  <AppLayout>
    <div class="pagina-autenticacion">
      <h1>SIAM</h1>

      <p>{{ t("common.systemName") }}</p>

      <!-- Comprobación de sesión -->
      <p v-if="comprobando" role="status">
        {{ t("auth.checking") }}
      </p>

      <!-- Área interna -->
      <section
        v-else-if="usuario"
        aria-labelledby="titulo-interno"
      >
        <h2 id="titulo-interno">
          {{ t("auth.internalArea") }}
        </h2>

        <p>
          {{ t("auth.loggedInAs", { name: usuario.full_name }) }}
        </p>

        <p>
          {{ t("auth.notImplemented") }}
        </p>

        <button
          type="button"
          :disabled="enviando"
          @click="cerrarSesion"
        >
          {{ enviando ? t("auth.loggingOut") : t("auth.logout") }}
        </button>
      </section>

      <!-- Formulario de inicio de sesión -->
      <form
        v-else
        :aria-busy="enviando"
        @submit.prevent="ingresar"
      >
        <h2>{{ t("auth.loginTitle") }}</h2>

        <label for="correo">
          {{ t("auth.email") }}
        </label>

        <input
          id="correo"
          v-model.trim="correo"
          name="email"
          type="email"
          autocomplete="username"
          maxlength="254"
          required
          :disabled="enviando"
        />

        <label for="contrasena">
          {{ t("auth.password") }}
        </label>

        <input
          id="contrasena"
          v-model="contrasena"
          name="password"
          type="password"
          autocomplete="current-password"
          required
          :disabled="enviando"
        />

        <button
          type="submit"
          :disabled="enviando"
        >
          {{ enviando ? t("auth.loggingIn") : t("auth.login") }}
        </button>
      </form>

      <!-- Mensajes del sistema -->
      <p role="status">
        {{ enviando ? t("common.processing") : "" }}
      </p>

      <p role="alert" class="error">
        {{ error ? t(error) : "" }}
      </p>
    </div>
  </AppLayout>
</template>

<style scoped>
/* Contenedor del inicio de sesión */
.pagina-autenticacion {
  width: 100%;
  max-width: 448px;
  min-width: 0;
  margin: 24px auto;
  overflow-wrap: anywhere;
}

h1 {
  color: #1f4a5b;
}

/* Formulario */
form {
  display: grid;
  gap: 12px;
  width: 100%;
}

/* Campos y botones */
input,
button {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid #666;
  border-radius: 6px;
  font: inherit;
}

input {
  background: #fff;
  color: #111;
}

button {
  background: #1f4a5b;
  color: #fff;
  cursor: pointer;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

/* Mensajes de error */
.error {
  color: #8b1d1d;
}

/* Adaptación para celulares */
@media (max-width: 767px) {
  .pagina-autenticacion {
    margin: 8px auto;
  }
}
</style>
