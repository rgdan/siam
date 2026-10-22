
import { createI18n } from "vue-i18n"

// Traducciones de la interfaz de SIAM.
const mensajes = {
  es: {
    common: {
      systemName: "Sistema de Información y Analítica Museal",
      home: "Inicio",
      museumInfo: "Información del museo",
      events: "Eventos",
      menu: "Menú",
      closeMenu: "Cerrar menú",
      processing: "Procesando solicitud…",
      lightMode: "Modo claro",
      darkMode: "Modo oscuro",
    },

    auth: {
      loginTitle: "Inicio de sesión",
      email: "Correo electrónico",
      password: "Contraseña",
      login: "Ingresar",
      loggingIn: "Ingresando…",
      logout: "Cerrar sesión",
      loggingOut: "Cerrando sesión…",
      checking: "Comprobando sesión…",
      internalArea: "Área interna",
      loggedInAs: "Sesión iniciada como {name}.",
      notImplemented: "Las funciones internas todavía no están implementadas.",
      invalidCredentials: "Correo o contraseña incorrectos",
      sessionUnavailable: "La sesión no está disponible. Intente ingresar de nuevo.",
      loginError: "No se pudo iniciar sesión. Revise la conexión y vuelva a intentarlo.",
      logoutError: "No se pudo confirmar el cierre de sesión. Revise la conexión e inténtelo de nuevo.",
      sessionError: "No se pudo comprobar la sesión. Revise la conexión y recargue la página.",
    },
  },

  en: {
    common: {
      systemName: "Museum Information and Analytics System",
      home: "Home",
      museumInfo: "Museum information",
      events: "Events",
      menu: "Menu",
      closeMenu: "Close menu",
      processing: "Processing request…",
      lightMode: "Light mode",
      darkMode: "Dark mode",
    },

    auth: {
      loginTitle: "Sign in",
      email: "Email address",
      password: "Password",
      login: "Sign in",
      loggingIn: "Signing in…",
      logout: "Sign out",
      loggingOut: "Signing out…",
      checking: "Checking session…",
      internalArea: "Internal area",
      loggedInAs: "Signed in as {name}.",
      notImplemented: "Internal features have not been implemented yet.",
      invalidCredentials: "Incorrect email or password",
      sessionUnavailable: "The session is unavailable. Please sign in again.",
      loginError: "Could not sign in. Check the connection and try again.",
      logoutError: "Could not confirm sign out. Check the connection and try again.",
      sessionError: "Could not check the session. Check the connection and reload the page.",
    },
  },
}

// Recupera el idioma elegido anteriormente.
function obtenerIdiomaInicial() {
  try {
    const guardado = localStorage.getItem("siam-idioma")
    if (guardado === "es" || guardado === "en") {
      return guardado
    }
  } catch {
    // Si el almacenamiento no está disponible, usar español.
  }

  return "es"
}

export const i18n = createI18n({
  legacy: false,
  locale: obtenerIdiomaInicial(),
  fallbackLocale: "es",
  messages: mensajes,
  missingWarn: true,
  fallbackWarn: true,
})

// Guarda el idioma seleccionado.
export function cambiarIdioma(idioma) {
  if (idioma !== "es" && idioma !== "en") return

  i18n.global.locale.value = idioma
  document.documentElement.lang = idioma

  try {
    localStorage.setItem("siam-idioma", idioma)
  } catch {
    // La interfaz seguirá funcionando sin almacenamiento.
  }
}


function obtenerConfiguracionRegional() {
  return i18n.global.locale.value === "en" ? "en-US" : "es-CR"
}

// Formatea fechas según el idioma seleccionado.
export function formatearFecha(fecha) {
  return new Intl.DateTimeFormat(
    obtenerConfiguracionRegional(),
    { dateStyle: "long" }
  ).format(new Date(fecha))
}

// Formatea horas según el idioma seleccionado.
export function formatearHora(fecha) {
  return new Intl.DateTimeFormat(
    obtenerConfiguracionRegional(),
    { timeStyle: "short" }
  ).format(new Date(fecha))
}

// Formatea números según el idioma seleccionado.
export function formatearNumero(numero) {
  return new Intl.NumberFormat(
    obtenerConfiguracionRegional()
  ).format(numero)
}

