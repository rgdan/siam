
import { createI18n } from "vue-i18n"

// Traducciones de la interfaz de SIAM.
const mensajes = {
  es: {
    common: {
      systemName: "Sistema de Información y Analítica Museal",
      museumSystem: "Sistema museal",
      public: "Público",
      information: "Información",
      navigation: "Navegación principal",
      language: "Idioma",
      theme: "Tema",
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

    users: {
      title: "Usuarios", create: "Crear cuenta", refresh: "Actualizar lista",
      loading: "Cargando cuentas…", empty: "No hay cuentas. Cree una para comenzar.",
      edit: "Editar cuenta", editAccount: "Editar la cuenta de {name}",
      fullName: "Nombre completo", role: "Rol", status: "Estado",
      active: "Activa", inactive: "Inactiva", save: "Guardar cuenta", cancel: "Cancelar",
      delete: "Eliminar cuenta", resetPassword: "Nueva contraseña (opcional)",
      passwordRule: "Al menos 8 caracteres, con letras y números.",
      passwordOptional: "Déjela vacía para conservar la actual. Una nueva contraseña requiere al menos 8 caracteres, letras y números; cerrará las sesiones de esta persona.",
      saved: "Cuenta guardada.", deleted: "Cuenta eliminada.",
      deactivated: "La cuenta tiene registros relacionados y fue desactivada.",
      confirmDelete: "¿Confirma la eliminación de esta cuenta?",
      deleteWarning: "Si tiene registros relacionados, se desactivará para conservarlos. Esta operación no elimina su historial.",
      loadError: "No se pudo cargar la lista. Pulse Actualizar lista para volver a intentarlo.",
      saveError: "No se pudo confirmar la operación. Actualice la lista antes de volver a intentarlo.",
      noAccess: "Sin acceso", noAccessDescription: "Su cuenta no tiene permiso para abrir esta sección.",
      chooseSection: "Seleccione una sección del menú.",
    },
    audit: {
      title: "Bitácora", refresh: "Actualizar bitácora", loading: "Cargando bitácora…",
      total: "Registros: {count}", empty: "No se encontraron registros.",
      filters: "Filtros", userFilter: "Correo del usuario", actionType: "Tipo de acción",
      allActions: "Todos los tipos",
      dateFrom: "Desde", dateTo: "Hasta", applyFilters: "Filtrar", clearFilters: "Limpiar filtros",
      invalidFilters: "Revise los filtros y pulse Filtrar otra vez. Indique un correo válido y una fecha final que no sea anterior a la inicial.",
      error: "No se pudo cargar la bitácora. Pulse Actualizar bitácora para volver a intentarlo.",
      actor: "Usuario", noUser: "Sin usuario identificado", entity: "Entidad",
      changes: "Ver cambios", noChanges: "Sin cambios de campos registrados.",
      previous: "Anterior", next: "Siguiente", page: "Página {page}",
      actions: {
        create: "Creación", modify: "Modificación", decommission: "Baja",
        sensitive_read: "Acceso sensible", login: "Inicio de sesión", failed_login: "Inicio de sesión fallido",
      },
    },
    roles: {
      guarda: "Guarda", coordinador: "Coordinador", museologo: "Museólogo",
      administrador_general: "Administrador general", administrador_sistema: "Administrador de sistema",
    },

    museum: {
      welcome: "Conozca la historia y el patrimonio cultural de nuestro museo.",
      history: "Historia del museo",
      location: "Ubicación",
      hours: "Horario de atención",
      openDays: "Días de apertura por semana",
      admission: "Entrada al museo",
      free: "Gratuita",
      askAdmission: "Consultar",
      noHours: "No hay horarios disponibles.",
      hoursDescription: "Consulte nuestros días y horarios de atención al público.",
      viewSchedule: "Ver horarios",
      schedule: "Horarios",
      scheduleDescription: "Horario de apertura y cierre para cada día de la semana.",
      day: "Día",
      opening: "Apertura",
      closing: "Cierre",
      status: "Estado",
      open: "Abierto",
      closed: "Cerrado",
      backHome: "Volver al inicio",

      days: {
        sunday: "Domingo",
        monday: "Lunes",
        tuesday: "Martes",
        wednesday: "Miércoles",
        thursday: "Jueves",
        friday: "Viernes",
        saturday: "Sábado",
      },
    },
  },

  en: {
    common: {
      systemName: "Museum Information and Analytics System",
      museumSystem: "Museum system",
      public: "Public",
      information: "Information",
      navigation: "Main navigation",
      language: "Language",
      theme: "Theme",
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

    users: {
      title: "Users", create: "Create account", refresh: "Refresh list",
      loading: "Loading accounts…", empty: "No accounts yet. Create one to begin.",
      edit: "Edit account", editAccount: "Edit {name}'s account",
      fullName: "Full name", role: "Role", status: "Status",
      active: "Active", inactive: "Inactive", save: "Save account", cancel: "Cancel",
      delete: "Delete account", resetPassword: "New password (optional)",
      passwordRule: "At least 8 characters, with letters and numbers.",
      passwordOptional: "Leave blank to keep the current password. A new password needs at least 8 characters, letters and numbers; it will end this person's sessions.",
      saved: "Account saved.", deleted: "Account deleted.",
      deactivated: "The account has related records and was deactivated.",
      confirmDelete: "Confirm deletion of this account?",
      deleteWarning: "Accounts with related records will be deactivated to preserve them. This operation does not delete their history.",
      loadError: "Could not load accounts. Select Refresh list to try again.",
      saveError: "Could not confirm the operation. Refresh the list before trying again.",
      noAccess: "Access denied", noAccessDescription: "Your account does not have permission to open this section.",
      chooseSection: "Select a section from the menu.",
    },
    audit: {
      title: "Audit log", refresh: "Refresh audit log", loading: "Loading audit log…",
      total: "Records: {count}", empty: "No matching audit records.",
      filters: "Filters", userFilter: "User email", actionType: "Action type",
      allActions: "All action types",
      dateFrom: "From", dateTo: "To", applyFilters: "Filter", clearFilters: "Clear filters",
      invalidFilters: "Check the filters and select Filter again. Enter a valid email and an end date that is not before the start date.",
      error: "Could not load the audit log. Select Refresh audit log to try again.",
      actor: "User", noUser: "Unidentified user", entity: "Entity",
      changes: "View changes", noChanges: "No field changes recorded.",
      previous: "Previous", next: "Next", page: "Page {page}",
      actions: {
        create: "Creation", modify: "Modification", decommission: "Decommission",
        sensitive_read: "Sensitive access", login: "Sign in", failed_login: "Failed sign in",
      },
    },
    roles: {
      guarda: "Guard", coordinador: "Coordinator", museologo: "Museologist",
      administrador_general: "General administrator", administrador_sistema: "System administrator",
    },

    museum: {
      welcome: "Discover the history and cultural heritage of our museum.",
      history: "Museum history",
      location: "Location",
      hours: "Opening hours",
      openDays: "Opening days per week",
      admission: "Museum admission",
      free: "Free",
      askAdmission: "Enquire",
      noHours: "No opening hours available.",
      hoursDescription: "Check our opening days and visiting hours.",
      viewSchedule: "View opening hours",
      schedule: "Opening hours",
      scheduleDescription: "Opening and closing times for each day of the week.",
      day: "Day",
      opening: "Opens",
      closing: "Closes",
      status: "Status",
      open: "Open",
      closed: "Closed",
      backHome: "Back to home",

      days: {
        sunday: "Sunday",
        monday: "Monday",
        tuesday: "Tuesday",
        wednesday: "Wednesday",
        thursday: "Thursday",
        friday: "Friday",
        saturday: "Saturday",
      },
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
