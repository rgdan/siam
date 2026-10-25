// El navegador administra la cookie de sesión; nunca guardamos credenciales en JavaScript.
export function solicitar(ruta, opciones = {}) {
  return fetch(`${import.meta.env.VITE_API_BASE_URL}${ruta}`, {
    ...opciones,
    credentials: "include",
    signal: AbortSignal.timeout(5000),
  })
}

// Django exige un token CSRF también para modificar o eliminar cuentas.
export async function enviar(ruta, datos = {}, metodo = "POST") {
  const respuesta = await solicitar("auth/csrf/")
  if (!respuesta.ok) throw new Error()
  const { csrfToken } = await respuesta.json()
  if (typeof csrfToken !== "string") throw new Error()
  return solicitar(ruta, {
    method: metodo,
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
    body: JSON.stringify(datos),
  })
}
