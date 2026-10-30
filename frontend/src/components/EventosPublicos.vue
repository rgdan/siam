
<script setup>
import { onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { solicitar } from "../api.js"
import { formatearFecha, formatearHora } from "../i18n/index.js"

const { t } = useI18n({ useScope: "global" })

const eventos = ref([])
const cargando = ref(false)
const error = ref(false)

async function cargarEventos() {
  cargando.value = true
  error.value = false

  try {
    const respuesta = await solicitar("events/")

    if (!respuesta.ok) {
      throw new Error("No se pudieron consultar los eventos.")
    }

    const datos = await respuesta.json()

    if (!Array.isArray(datos)) {
      throw new Error("La respuesta no contiene una lista de eventos.")
    }

    eventos.value = datos
      .filter(evento =>
        evento.tipo === "publico" &&
        new Date(evento.fecha).getTime() >= Date.now()
      )
      .sort((a, b) => new Date(a.fecha) - new Date(b.fecha))

  } catch {
    error.value = true
    eventos.value = []
  } finally {
    cargando.value = false
  }
}

onMounted(cargarEventos)
</script>

<template>
  <section class="eventos-publicos">
    <header class="encabezado-eventos">
      <div>
        <h1>{{ t("publicEvents.title") }}</h1>
        <p>{{ t("publicEvents.description") }}</p>
      </div>

      <button
        type="button"
        :disabled="cargando"
        @click="cargarEventos"
      >
        {{ t("publicEvents.refresh") }}
      </button>
    </header>

    <p v-if="cargando" role="status">
      {{ t("publicEvents.loading") }}
    </p>

    <p v-else-if="error" role="alert" class="mensaje-error">
      {{ t("publicEvents.loadError") }}
    </p>

    <p v-else-if="eventos.length === 0" role="status">
      {{ t("publicEvents.empty") }}
    </p>

    <div v-else class="lista-eventos">
      <article
        v-for="evento in eventos"
        :key="evento.id"
        class="tarjeta-evento"
      >
        <div class="fecha-evento">
          <span>{{ formatearFecha(evento.fecha) }}</span>
          <span>{{ formatearHora(evento.fecha) }}</span>
        </div>

        <h2>{{ evento.descripcion }}</h2>

        <p>
          <strong>{{ t("publicEvents.location") }}:</strong>
          {{ evento.ubicacion }}
        </p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.eventos-publicos {
  width: 100%;
  max-width: 1000px;
  min-width: 0;
  margin: 0 auto;
  color: var(--color-texto);
}

.encabezado-eventos {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 28px;
}

.encabezado-eventos h1 {
  margin-top: 0;
  color: var(--color-enlace);
}

.encabezado-eventos p {
  line-height: 1.6;
}

button {
  box-sizing: border-box;
  min-height: 44px;
  padding: 10px 16px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  background: var(--color-header);
  color: #ffffff;
  font: inherit;
  cursor: pointer;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.lista-eventos {
  display: grid;
  gap: 18px;
}

.tarjeta-evento {
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--color-borde);
  border-radius: 10px;
  background: var(--color-control);
  overflow-wrap: anywhere;
}

.fecha-evento {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  font-weight: 600;
  color: var(--color-enlace);
}

.tarjeta-evento h2 {
  margin: 16px 0;
  font-size: 1.15rem;
}

.tarjeta-evento p {
  margin-bottom: 0;
  line-height: 1.6;
}

.mensaje-error {
  color: var(--color-error);
}

@media (max-width: 767px) {
  .encabezado-eventos {
    flex-direction: column;
  }

  .tarjeta-evento {
    padding: 16px;
  }

  .encabezado-eventos button {
    width: 100%;
  }
}
</style>
