
import { ref } from "vue"

function obtenerTemaInicial() {
  try {
    const guardado = localStorage.getItem("siam-tema")

    if (guardado === "claro" || guardado === "oscuro") {
      return guardado
    }
  } catch {
    // Continuar con la preferencia del sistema.
  }

  if (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "oscuro"
  }

  return "claro"
}

export const tema = ref(obtenerTemaInicial())

export function cambiarTema(nuevoTema) {
  if (nuevoTema !== "claro" && nuevoTema !== "oscuro") return

  tema.value = nuevoTema
  document.documentElement.dataset.theme = nuevoTema

  try {
    localStorage.setItem("siam-tema", nuevoTema)
  } catch {
    // La interfaz sigue funcionando sin almacenamiento.
  }
}

export function inicializarTema() {
  document.documentElement.dataset.theme = tema.value
}
