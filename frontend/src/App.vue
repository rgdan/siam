<script setup>
import { onMounted, ref } from "vue"

const estado = ref("Conectando…")

onMounted(async () => {
  try {
    const respuesta = await fetch(`${import.meta.env.VITE_API_BASE_URL}health/`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!respuesta.ok) throw new Error()

    const datos = await respuesta.json()
    estado.value = datos.estado === "ok" ? "Conectado" : "La API no confirmó la conexión."
  } catch {
    estado.value = "No se pudo conectar. Revisa la URL de la API y el backend, y recarga la página."
  }
})
</script>

<template>
  <main>
    <h1>SIAM</h1>
    <p>Borrador técnico sin diseño visual.</p>
    <p role="status">{{ estado }}</p>
  </main>
</template>

<style>
body {
  margin: 0;
  background: #fff;
  color: #111;
  font-family: system-ui, sans-serif;
}

main {
  max-width: 40rem;
  margin: 3rem auto;
  padding: 0 1rem;
  overflow-wrap: anywhere;
}

h1 {
  color: #1f4a5b;
}
</style>
