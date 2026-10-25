<script setup>
import { ref } from "vue"
import { useI18n } from "vue-i18n"
import { cambiarIdioma } from "../i18n/index.js"
import { tema, cambiarTema } from "../theme/index.js"

const props = defineProps({
  usuario: { type: Object, default: null },
  rutaActual: { type: String, default: "/" },
})
const { t, locale } = useI18n({ useScope: "global" })
const menuAbierto = ref(false)
const botonMenu = ref(null)

// El menú móvil se cierra al elegir un destino o pulsar Escape.
function cerrarMenu() {
  menuAbierto.value = false
  botonMenu.value?.focus()
}

// Conserva la preferencia de idioma mediante el módulo existente.
function seleccionarIdioma(evento) {
  cambiarIdioma(evento.target.value)
}

// Guarda el tema elegido igual que la preferencia de idioma.
function seleccionarTema(evento) {
  cambiarTema(evento.target.value)
}
</script>

<template>
  <div class="app-layout">
    <aside class="barra-lateral" @keydown.esc="cerrarMenu">
      <header class="marca">
        <a class="app-logo" href="/" @click="cerrarMenu">
          <span class="marca-inicial" aria-hidden="true">S</span>
          <span>SIAM<small>{{ t("common.museumSystem") }}</small></span>
        </a>
        <p>{{ usuario ? t(`roles.${usuario.role}`) : t("common.public") }}</p>
        <button
          ref="botonMenu"
          class="menu-boton"
          type="button"
          aria-controls="navegacion-lateral"
          :aria-expanded="menuAbierto"
          @click="menuAbierto = !menuAbierto"
        >{{ menuAbierto ? t("common.closeMenu") : t("common.menu") }}</button>
      </header>

      <div id="navegacion-lateral" class="contenido-lateral" :class="{ abierto: menuAbierto }">
        <nav :aria-label="t('common.navigation')">
          <a
            href="/"
            :aria-current="['/', '/informacion', '/horarios'].includes(props.rutaActual) ? 'page' : undefined"
            @click="cerrarMenu"
          >{{ t("common.information") }}</a>
          <a
            v-if="usuario"
            href="/interno"
            :aria-current="props.rutaActual === '/interno' ? 'page' : undefined"
            @click="cerrarMenu"
          >{{ t("auth.internalArea") }}</a>
          <a
            v-if="usuario?.permissions?.includes('usuarios.consultar')"
            href="/interno/usuarios"
            :aria-current="props.rutaActual === '/interno/usuarios' ? 'page' : undefined"
            @click="cerrarMenu"
          >{{ t("users.title") }}</a>
        </nav>

        <div class="preferencias">
          <div class="campo-preferencia">
            <label for="idioma">{{ t("common.language") }}</label>
            <select id="idioma" :value="locale" @change="seleccionarIdioma">
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="campo-preferencia">
            <label for="tema">{{ t("common.theme") }}</label>
            <select id="tema" :value="tema" @change="seleccionarTema">
              <option value="claro">{{ t("common.lightMode") }}</option>
              <option value="oscuro">{{ t("common.darkMode") }}</option>
            </select>
          </div>
          <a class="acceso-interno" href="/interno" @click="cerrarMenu">
            {{ usuario ? t("auth.internalArea") : t("auth.login") }}
          </a>
        </div>
      </div>
    </aside>

    <main class="app-contenido">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.app-layout { min-height: 100dvh; }
.barra-lateral {
  --color-foco: #ffffff;
  position: fixed;
  inset: 0 auto 0 0;
  width: 260px;
  display: flex;
  flex-direction: column;
  background: var(--color-header);
  color: #ffffff;
}
.marca { padding: 20px 24px 28px; border-bottom: 1px solid #315168; }
.app-logo { display: inline-flex; align-items: center; gap: 12px; min-height: 44px; color: #ffffff; text-decoration: none; font: bold 20px Georgia, serif; }
.marca-inicial { display: grid; place-items: center; width: 32px; height: 32px; background: var(--color-acento); border-radius: 7px; font-size: 16px; }
.app-logo small { display: block; margin-top: 3px; color: #b8c9d6; font: 11px system-ui, sans-serif; }
.marca p { margin: 8px 0 0; color: #b8c9d6; font-size: 12px; }
.contenido-lateral { display: flex; flex: 1; flex-direction: column; min-height: 0; overflow-y: auto; }
nav { padding-top: 12px; }
nav a { display: flex; align-items: center; min-height: 44px; padding: 12px 24px; border-left: 3px solid transparent; color: #b8c9d6; font-size: 14px; text-decoration: none; }
nav a:hover { background: var(--color-header-hover); color: #ffffff; }
nav a[aria-current="page"] { border-left-color: #ed4b3b; background: var(--color-header-hover); color: #ffffff; }
.preferencias { display: grid; gap: 12px; margin-top: auto; padding: 20px 24px; border-top: 1px solid #315168; }
.campo-preferencia { display: grid; gap: 8px; font-size: 13px; }
select, button, .acceso-interno { min-height: 44px; padding: 10px 12px; border: 1px solid #8aa4b7; border-radius: 7px; font: inherit; }
select { width: 100%; color: #ffffff; background: var(--color-header); }
button { cursor: pointer; }
.acceso-interno { display: grid; place-items: center; border-color: var(--color-acento); background: var(--color-acento); color: #ffffff; font-size: 13px; font-weight: 600; text-decoration: none; }
.menu-boton { display: none; background: transparent; color: #ffffff; }
.app-contenido { min-width: 0; margin-left: 260px; padding: 26px 32px 48px; }
@media (max-width: 800px) {
  .barra-lateral { position: static; width: 100%; }
  .marca { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 20px; }
  .marca p { display: none; }
  .menu-boton { display: block; }
  .contenido-lateral { display: none; }
  .contenido-lateral.abierto { display: flex; }
  .preferencias { margin-top: 20px; }
  .app-contenido { margin-left: 0; padding: 24px 20px; }
}
@media (max-width: 400px) {
  .marca, .app-contenido { padding-inline: 16px; }
}
</style>
