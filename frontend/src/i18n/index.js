import { createI18n } from "vue-i18n"
import common from "./common.js"
import events from "./events.js"
import users from "./users.js"
import audit from "./audit.js"
import visitors from "./visitors.js"
import incidents from "./incidents.js"
import museum from "./museum.js"
import reports from "./reports.js"
import privacy from "./privacy.js"
import collection from "./collection.js"
import configuration from "./configuration.js"

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
  messages: {
    es: {
      ...common.es,
      ...events.es,
      ...users.es,
      ...audit.es,
      ...visitors.es,
      ...incidents.es,
      ...museum.es,
      ...reports.es,
      ...privacy.es,
      ...collection.es,
      ...configuration.es,
    },
    en: {
      ...common.en,
      ...events.en,
      ...users.en,
      ...audit.en,
      ...visitors.en,
      ...incidents.en,
      ...museum.en,
      ...reports.en,
      ...privacy.en,
      ...collection.en,
      ...configuration.en,
    },
  },
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

// Obtiene el formato regional del idioma seleccionado.
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
