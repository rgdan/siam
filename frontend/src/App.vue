
<script setup>
import { onMounted, ref } from "vue"
import AppLayout from "./components/AppLayout.vue"

// Vue actualiza la pantalla cuando cambia alguno de estos valores.
const usuario = ref(null)
const correo = ref("")
const contrasena = ref("")
const comprobando = ref(true)
const enviando = ref(false)
const error = ref("")

// Todas las solicitudes usan la URL configurada, incluyen cookies y esperan hasta 5 segundos.
function solicitar(ruta, opciones = {}) {
  return fetch(`${import.meta.env.VITE_API_BASE_URL}${ruta}`, {
    ...opciones,
    credentials: "include",
    signal: AbortSignal.timeout(5000),
  })
}

// Obtiene un token CSRF vigente antes de cada POST, incluso después de recargar.
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

// Django confirma la identidad; la URL por sí sola no demuestra que exista una sesión.
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

// Envía las credenciales y consulta la cuenta; la contraseña se borra al terminar.
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
      error.value = "Correo o contraseña incorrectos"
      return
    }

    if (!respuesta.ok) throw new Error()

    await cargarSesion()

    if (!usuario.value) {
      error.value = "La sesión no está disponible. Intente ingresar de nuevo."
    }
  } catch {
    error.value = "No se pudo iniciar sesión. Revise la conexión y vuelva a intentarlo."
  } finally {
    contrasena.value = ""
    enviando.value = false
  }
}

// Conserva la sesión en pantalla hasta que Django confirme que terminó o ya no existe.
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
    error.value = "No se pudo confirmar el cierre de sesión. Revise la conexión e inténtelo de nuevo."
  } finally {
    enviando.value = false
  }
}

// Comprueba la sesión al abrir o recargar, sin mostrar antes el contenido interno.
onMounted(async () => {
  try {
    await cargarSesion()
  } catch {
    window.history.replaceState(null, "", "/login")
    error.value = "No se pudo comprobar la sesión. Revise la conexión y recargue la página."
  } finally {
    comprobando.value = false
  }
})
</script>

<template>
  <AppLayout>
    <div class="pagina-autenticacion">
      <h1>SIAM</h1>
      <p>Sistema de Información y Analítica Museal</p>

      <!-- Comprobación de sesión -->
      <p v-if="comprobando" role="status">
        Comprobando sesión…
      </p>

      <!-- Área interna -->
      <section
        v-else-if="usuario"
        aria-labelledby="titulo-interno"
      >
        <h2 id="titulo-interno">Área interna</h2>

        <p>
          Sesión iniciada como {{ usuario.full_name }}.
        </p>

        <p>
          Las funciones internas todavía no están implementadas.
        </p>

        <button
          type="button"
          :disabled="enviando"
          @click="cerrarSesion"
        >
          {{ enviando ? "Cerrando sesión…" : "Cerrar sesión" }}
        </button>
      </section>

      <!-- Formulario de inicio de sesión -->
      <form
        v-else
        :aria-busy="enviando"
        @submit.prevent="ingresar"
      >
        <h2>Inicio de sesión</h2>

        <label for="correo">
          Correo electrónico
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
          Contraseña
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
          {{ enviando ? "Ingresando…" : "Ingresar" }}
        </button>
      </form>

      <!-- Mensajes del sistema -->
      <p role="status">
        {{ enviando ? "Procesando solicitud…" : "" }}
      </p>

      <p role="alert" class="error">
        {{ error }}
      </p>
    </div>
  </AppLayout>
</template>

<style scoped>
/* Contenedor de inicio de sesión */
.pagina-autenticacion {
  width: 100%;
  max-width: 448px;
  min-width: 0;
  margin: 24px auto;
  overflow-wrap: anywhere;
}

/* Título */
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
