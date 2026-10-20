<script setup>
import { onMounted, ref } from "vue"

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
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
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
    if (!datos.id || typeof datos.full_name !== "string") throw new Error()
    usuario.value = datos
  }
  window.history.replaceState(null, "", usuario.value ? "/interno" : "/login")
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
    if (!usuario.value) error.value = "La sesión no está disponible. Intente ingresar de nuevo."
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
    if (!respuesta.ok && respuesta.status !== 401) throw new Error()
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
  <main>
    <h1>SIAM</h1>
    <p>Borrador técnico sin diseño visual.</p>
    <!-- Muestra la espera, el área interna o el formulario según el estado de la sesión. -->
    <p v-if="comprobando" role="status">Comprobando sesión…</p>
    <section v-else-if="usuario" aria-labelledby="titulo-interno">
      <h2 id="titulo-interno">Área interna</h2>
      <p>Sesión iniciada como {{ usuario.full_name }}.</p>
      <p>Las funciones internas todavía no están implementadas.</p>
      <button type="button" :disabled="enviando" @click="cerrarSesion">
        {{ enviando ? "Cerrando sesión…" : "Cerrar sesión" }}
      </button>
    </section>
    <form v-else :aria-busy="enviando" @submit.prevent="ingresar">
      <h2>Inicio de sesión</h2>
      <label for="correo">Correo electrónico</label>
      <input id="correo" v-model.trim="correo" name="email" type="email"
        autocomplete="username" maxlength="254" required :disabled="enviando" />
      <label for="contrasena">Contraseña</label>
      <input id="contrasena" v-model="contrasena" name="password" type="password"
        autocomplete="current-password" required :disabled="enviando" />
      <button type="submit" :disabled="enviando">
        {{ enviando ? "Ingresando…" : "Ingresar" }}
      </button>
    </form>
    <!-- Anuncia el progreso y los errores también a los lectores de pantalla. -->
    <p role="status">{{ enviando ? "Procesando solicitud…" : "" }}</p>
    <p role="alert" class="error">{{ error }}</p>
  </main>
</template>

<style>
/* Estilos compartidos por el formulario y el área interna provisional. */
body {
  margin: 0;
  background: #fff;
  color: #111;
  font-family: system-ui, sans-serif;
  line-height: 1.5;
}

/* Limita el ancho de lectura y permite ajustar el contenido a pantallas pequeñas. */
main {
  max-width: 28rem;
  margin: clamp(1rem, 5vw, 3rem) auto;
  padding: 0 1rem;
  overflow-wrap: anywhere;
}

h1 {
  color: #1f4a5b;
}

form {
  display: grid;
  gap: 0.75rem;
}

/* Mantiene los controles dentro del formulario y con altura suficiente para pulsarlos. */
input,
button {
  box-sizing: border-box;
  min-width: 0;
  width: 100%;
  min-height: 2.75rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #666;
  font: inherit;
}

input {
  color: #111;
  background: #fff;
}

button {
  color: #fff;
  background: #1f4a5b;
  cursor: pointer;
}

button:disabled {
  background: #555;
  cursor: wait;
}

/* Indica qué control tiene el foco al navegar con el teclado. */
:focus-visible {
  outline: 3px solid #1f4a5b;
  outline-offset: 3px;
}

.error {
  color: #8b1d1d;
}
</style>
