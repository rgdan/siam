<script setup>
import { useI18n } from "vue-i18n"

const { t, tm } = useI18n({ useScope: "global" })
</script>

<template>
  <article class="politica-privacidad" aria-labelledby="titulo-privacidad">
    <h1 id="titulo-privacidad">{{ t('privacy.titulo') }}</h1>
    <p>{{ t('privacy.fecha') }}</p>
    <p>{{ t('privacy.introduccion') }}</p>

    <section v-for="(seccion, indice) in tm('privacy.secciones')" :key="indice">
      <h2>{{ t(`privacy.secciones[${indice}].titulo`) }}</h2>
      <p v-for="(_, parrafo) in seccion.parrafos" :key="parrafo">{{ t(`privacy.secciones[${indice}].parrafos[${parrafo}]`) }}</p>
    </section>

    <section>
      <h2>{{ t('privacy.recursos') }}</h2>
      <p>{{ t('privacy.reclamos') }}</p>
      <ul>
        <li><a href="https://formatos.inamu.go.cr/SIDOC/DOCS/ley_8968.pdf">{{ t('privacy.ley') }}</a></li>
        <li><a href="https://www.prodhab.go.cr/tramites%20y%20servicios/index.aspx">{{ t('privacy.prodhab') }}</a></li>
      </ul>
    </section>
  </article>
</template>

<style scoped>
.politica-privacidad {
  max-width: 72ch;
  margin-inline: auto;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

h1 { line-height: 1.2; }
h2 { margin-top: 2rem; line-height: 1.3; }
a { color: var(--color-enlace); }
li + li { margin-top: 0.75rem; }
</style>
