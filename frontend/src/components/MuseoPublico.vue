
<script setup>
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { museoProvisional } from "../data/museo.js"

const { t, locale } = useI18n({ useScope: "global" })

// Vista que se muestra según la dirección del navegador.
const props = defineProps({
  vistaInicial: {
    type: String,
    default: "inicio",
  },
})

const dias = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
]

// Información general según el idioma.
const historia = computed(() =>
  museoProvisional.historia[locale.value] ??
  museoProvisional.historia.es
)

const ubicacion = computed(() =>
  museoProvisional.ubicacion[locale.value] ??
  museoProvisional.ubicacion.es
)

// Formato regional de las horas.
function formatearHorario(hora) {
  if (!hora) return "—"

  const [horas, minutos] = hora.split(":").map(Number)

  const fecha = new Date(2026, 0, 1, horas, minutos)

  return new Intl.DateTimeFormat(
    locale.value === "en" ? "en-US" : "es-CR",
    {
      hour: "numeric",
      minute: "2-digit",
    }
  ).format(fecha)
}

// Horarios traducidos y preparados para la tabla.
const horarios = computed(() =>
  museoProvisional.horarios.map((horario) => ({
    ...horario,
    nombre: t(`museum.days.${dias[horario.dia]}`),
    cerrado: !horario.apertura || !horario.cierre,
    aperturaFormateada: formatearHorario(horario.apertura),
    cierreFormateado: formatearHorario(horario.cierre),
  }))
)
</script>

<template>
  <div class="museo-publico">
    <!-- Página de información general -->
    <template v-if="props.vistaInicial === 'inicio'">
      <section class="seccion-museo">
        <h1>{{ museoProvisional.nombre }}</h1>
        <p>{{ t("museum.welcome") }}</p>
      </section>

      <section class="seccion-museo">
        <h2>{{ t("museum.history") }}</h2>
        <p>{{ historia }}</p>
      </section>

      <section class="seccion-museo">
        <h2>{{ t("museum.location") }}</h2>
        <p>{{ ubicacion }}</p>
      </section>

      <section class="seccion-museo">
        <h2>{{ t("museum.hours") }}</h2>
        <p>{{ t("museum.hoursDescription") }}</p>

        <a class="boton-principal" href="/horarios">
          {{ t("museum.viewSchedule") }}
        </a>
      </section>
    </template>

    <!-- Página de horarios -->
    <section v-else class="seccion-museo">
      <h1>{{ t("museum.schedule") }}</h1>
      <p>{{ t("museum.scheduleDescription") }}</p>

      <div class="tabla-responsive">
        <table>
          <thead>
            <tr>
              <th scope="col">{{ t("museum.day") }}</th>
              <th scope="col">{{ t("museum.opening") }}</th>
              <th scope="col">{{ t("museum.closing") }}</th>
              <th scope="col">{{ t("museum.status") }}</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="horario in horarios" :key="horario.dia">
              <th scope="row">{{ horario.nombre }}</th>

              <td>{{ horario.aperturaFormateada }}</td>
              <td>{{ horario.cierreFormateado }}</td>

              <td>
                {{ horario.cerrado
                  ? t("museum.closed")
                  : t("museum.open") }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <a class="boton-principal" href="/">
        {{ t("museum.backHome") }}
      </a>
    </section>
  </div>
</template>

<style scoped>
.museo-publico {
  width: 100%;
  min-width: 0;
  color: var(--color-texto);
}

.boton-principal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 10px 16px;
  border: 1px solid var(--color-borde);
  border-radius: 6px;
  background: var(--color-header);
  color: #ffffff;
  text-decoration: none;
  cursor: pointer;
}

.boton-principal:hover {
  background: var(--color-header-hover);
}

.seccion-museo {
  padding: 24px;
  margin-bottom: 20px;
  border: 1px solid var(--color-borde);
  border-radius: 8px;
  background: var(--color-superficie);
}

.seccion-museo h1,
.seccion-museo h2 {
  color: var(--color-enlace);
  margin-top: 0;
}

.seccion-museo p {
  line-height: 1.6;
}

.tabla-responsive {
  margin: 20px 0;
}

table {
  width: 100%;
}

th,
td {
  text-align: left;
}

@media (max-width: 767px) {
  .seccion-museo {
    padding: 16px;
  }
}
</style>
