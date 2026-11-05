<script setup>
import { onMounted, onUnmounted, ref, watch } from "vue"
import { useI18n } from "vue-i18n"
import Coleccion from "./components/Coleccion.vue"
import AppLayout from "./components/AppLayout.vue"
import MuseoPublico from "./components/MuseoPublico.vue"
import PoliticaPrivacidad from "./components/PoliticaPrivacidad.vue"
import EventosPublicos from "./components/EventosPublicos.vue"
import EventosInternos from "./components/EventosInternos.vue"
import ReporteAsistencia from "./components/ReporteAsistencia.vue"
import ReporteConsolidado from "./components/ReporteConsolidado.vue"
import Usuarios from "./components/Usuarios.vue"
import Bitacora from "./components/Bitacora.vue"
import RegistrarIngreso from "./components/RegistrarIngreso.vue"
import RegistrarIncidencia from "./components/RegistrarIncidencia.vue"
import RegistrarEvento from "./components/RegistrarEvento.vue"
import { solicitar, enviar } from "./api.js"

// Traducciones de SIAM.
const { t } = useI18n({ useScope: "global" })

// Navegación entre la información pública y la autenticación.
const rutaActual = ref(window.location.pathname)

function actualizarRuta() {
  rutaActual.value = window.location.pathname
}

function navegar(ruta) {
  if (window.location.pathname !== ruta) {
    window.history.pushState(null, "", ruta)
  }

  actualizarRuta()
}

// SIAM-13: la consulta de eventos públicos no requiere iniciar sesión.
const rutasPublicas = ["/", "/informacion", "/horarios", "/eventos", "/privacidad"]

const permisosPorRuta = {
  "/interno/coleccion": "piezas.crear",
  "/interno/usuarios": "usuarios.consultar",
  "/interno/bitacora": "bitacora.consultar",
  "/interno/ingresos": "visitantes.registrar",
  "/interno/incidencias": "incidencias.registrar",
  "/interno/eventos/registrar": "eventos.crear",

  // SIAM-17: reporte comparativo de asistencia.
  "/interno/reportes/asistencia": "eventos.generar_reportes",

  // SIAM-27: reportes consolidados.
  "/interno/reportes/consolidados": "reportes.ver_consolidados",
}

function esRutaPublica() {
  return rutasPublicas.includes(rutaActual.value)
}

// Estado de autenticación.
const usuario = ref(null)
const correo = ref("")
const contrasena = ref("")
const comprobando = ref(true)
const enviando = ref(false)
const error = ref("")
const accesoDenegado = ref(false)

// Una sesión expirada deja de mostrar inmediatamente los datos internos.
function sesionExpirada() {
  usuario.value = null
  navegar("/login")
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

  if (!esRutaPublica()) {
    if (!usuario.value) navegar("/login")
    else if (rutaActual.value === "/login") navegar("/interno")
  }
}

// El menú ayuda a navegar; la API vuelve a comprobar los permisos.
function puedeVerRuta() {
  if (rutaActual.value === "/interno") return true

  // SIAM-17 requiere el rol exacto de coordinador.
  if (rutaActual.value === "/interno/reportes/asistencia") {
    return (
      usuario.value?.role === "coordinador" &&
      usuario.value?.permissions?.includes(
        "eventos.generar_reportes"
      ) === true
    )
  }

  return usuario.value?.permissions?.includes(
    permisosPorRuta[rutaActual.value]
  ) === true
}

// Retira la sección si Django rechaza un permiso.
function denegarAcceso() {
  accesoDenegado.value = true
  cargarSesion().catch(sesionExpirada)
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
    navegar("/login")
  } catch {
    error.value = "auth.logoutError"
  } finally {
    enviando.value = false
  }
}

// Reconoce las rutas públicas sin exigir sesión.
async function comprobarSesion() {
  if (rutaActual.value === "/interno/eventos") {
    window.history.replaceState(null, "", "/eventos")
    actualizarRuta()
    return
  }

  comprobando.value = true

  if (esRutaPublica()) {
    try {
      await cargarSesion()
    } catch {
      usuario.value = null
    } finally {
      comprobando.value = false
    }

    return
  }

  accesoDenegado.value = false

  try {
    await cargarSesion()
  } catch {
    navegar("/login")
    error.value = "auth.sessionError"
  } finally {
    comprobando.value = false
  }
}

// También protege la navegación con Atrás y Adelante.
watch(rutaActual, comprobarSesion)

onMounted(() => {
  window.addEventListener("popstate", actualizarRuta)
  comprobarSesion()
})

onUnmounted(() => {
  window.removeEventListener("popstate", actualizarRuta)
})
</script>

<template>
  <AppLayout
    :usuario="usuario"
    :ruta-actual="rutaActual"
    :enviando="enviando"
    @cerrar-sesion="cerrarSesion"
  >
    <PoliticaPrivacidad v-if="rutaActual === '/privacidad'" />

    <template v-else-if="rutaActual === '/eventos'">
      <p v-if="comprobando" role="status">
        {{ t("auth.checking") }}
      </p>

      <EventosInternos
        v-else-if="usuario?.permissions?.includes('eventos.ver_privados')"
        @sesion-expirada="sesionExpirada"
        @sin-acceso="denegarAcceso"
      />

      <EventosPublicos v-else />
    </template>

    <!-- Información pública del museo -->
    <MuseoPublico
      v-else-if="esRutaPublica()"
      :key="rutaActual"
    />

    <!-- Autenticación y área interna -->
    <div
      v-else
      class="pagina-autenticacion"
      :class="{
        'pagina-administracion': permisosPorRuta[rutaActual] && usuario
      }"
    >
      <template v-if="rutaActual === '/interno'">
        <h1>SIAM</h1>
        <p>{{ t("common.systemName") }}</p>
      </template>

      <!-- Comprobación de sesión -->
      <p v-if="comprobando" role="status">
        {{ t("auth.checking") }}
      </p>

      <!-- Área interna -->
      <section
        v-else-if="usuario"
        :aria-labelledby="
          rutaActual === '/interno' ? 'titulo-interno' : undefined
        "
      >
        <template v-if="rutaActual === '/interno'">
          <h2 id="titulo-interno">
            {{ t("auth.internalArea") }}
          </h2>
          <p>
            {{ t("auth.loggedInAs", { name: usuario.full_name }) }}
          </p>
        </template>

        <section
          v-if="accesoDenegado || !puedeVerRuta()"
          role="alert"
        >
          <h2>{{ t("users.noAccess") }}</h2>
          <p>{{ t("users.noAccessDescription") }}</p>
          <a href="/interno">
            {{ t("auth.internalArea") }}
          </a>
        </section>

        <Coleccion
          v-else-if="rutaActual === '/interno/coleccion'"
          :usuario="usuario"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
        />

        <Usuarios
          v-else-if="rutaActual === '/interno/usuarios'"
          :usuario-actual="usuario"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
          @cuenta-actualizada="cargarSesion().catch(sesionExpirada)"
        />

        <Bitacora
          v-else-if="rutaActual === '/interno/bitacora'"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
        />

        <RegistrarIngreso
          v-else-if="rutaActual === '/interno/ingresos'"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
        />

        <RegistrarIncidencia
          v-else-if="rutaActual === '/interno/incidencias'"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
        />

        <RegistrarEvento
          v-else-if="rutaActual === '/interno/eventos/registrar'"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
        />

        <!-- SIAM-17: reporte comparativo de asistencia -->
        <ReporteAsistencia
          v-else-if="rutaActual === '/interno/reportes/asistencia'"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
        />

        <!-- SIAM-27: reportes consolidados -->
        <ReporteConsolidado
          v-else-if="rutaActual === '/interno/reportes/consolidados'"
          @sesion-expirada="sesionExpirada"
          @sin-acceso="denegarAcceso"
        />

        <p v-else>
          {{ t("users.chooseSection") }}
        </p>
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
    </div>

    <p v-if="error" role="alert" class="error">
      {{ t(error) }}
    </p>
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
  color: var(--color-texto);
}

.pagina-administracion {
  max-width: 900px;
}

.pagina-administracion:has(.collection) {
  max-width: 1180px;
  margin: 0 auto;
}

.pagina-administracion:has(.collection-list) {
  max-width: none;
  margin: 0;
}

/* SIAM-17: permitir más espacio para la tabla */
.pagina-administracion:has(.reporte-asistencia) {
  max-width: 1180px;
  margin: 0 auto;
}

/* SIAM-27: espacio para los reportes consolidados */
.pagina-administracion:has(.reporte-consolidado) {
  max-width: 1180px;
  margin: 0 auto;
}

h1 {
  color: var(--color-enlace);
}

a {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
}

form {
  display: grid;
  gap: 12px;
  width: 100%;
}

input,
button {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  font: inherit;
}

input {
  background: var(--color-control);
  color: var(--color-texto);
}

button {
  background: var(--color-header);
  color: #ffffff;
  cursor: pointer;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.error {
  color: var(--color-error);
}

@media (max-width: 767px) {
  .pagina-autenticacion {
    margin: 8px auto;
  }
}
</style>
