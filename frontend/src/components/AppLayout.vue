
<script setup>
import { ref } from "vue"
import { useI18n } from "vue-i18n"
import { cambiarIdioma } from "../i18n/index.js"
import { tema, cambiarTema } from "../theme/index.js"

// Control del menú móvil.
const menuAbierto = ref(false)

// Idioma y traducciones.
const { t, locale } = useI18n({ useScope: "global" })

defineProps({ usuario: { type: Object, default: null } })

// Navegación principal de SIAM.
const enlaces = [
  { nombre: "common.home", ruta: "/" },
  { nombre: "common.museumInfo", ruta: "/informacion" },
  { nombre: "museum.schedule", ruta: "/horarios" },
]


function cerrarMenu() {
  menuAbierto.value = false
}

function seleccionarIdioma(evento) {
  cambiarIdioma(evento.target.value)
}

function alternarTema() {
  cambiarTema(tema.value === "claro" ? "oscuro" : "claro")
}
</script>

<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-contenido">
        <a class="app-logo" href="/" @click="cerrarMenu">
          SIAM
        </a>

        <div class="header-acciones">
          <!-- Selector de idioma -->
          <div class="selector-idioma">
            <label for="idioma">
              {{ locale === "es" ? "Idioma" : "Language" }}
            </label>

            <select
              id="idioma"
              :value="locale"
              @change="seleccionarIdioma"
            >
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
          </div>

          <!-- Botón de modo claro y oscuro -->
          <button
            class="boton-tema"
            type="button"
            :aria-label="tema === 'claro' ? t('common.darkMode') : t('common.lightMode')"
            :title="tema === 'claro' ? t('common.darkMode') : t('common.lightMode')"
            :aria-pressed="tema === 'oscuro'"
            @click="alternarTema"
          >
            {{ tema === "claro" ? "☾" : "☀" }}
          </button>

          <!-- Menú móvil -->
          <button
            class="menu-boton"
            type="button"
            aria-controls="navegacion-principal"
            :aria-expanded="menuAbierto"
            @click="menuAbierto = !menuAbierto"
          >
            {{ menuAbierto ? t("common.closeMenu") : t("common.menu") }}
          </button>
        </div>

        <!-- Navegación -->
        <nav
          id="navegacion-principal"
          class="app-nav"
          :class="{ 'nav-abierta': menuAbierto }"
          :aria-label="locale === 'es' ? 'Navegación principal' : 'Main navigation'"
        >
          <a
            v-for="enlace in enlaces"
            :key="enlace.ruta"
            :href="enlace.ruta"
            @click="cerrarMenu"
          >
            {{ t(enlace.nombre) }}
          </a>
          <a href="/interno" @click="cerrarMenu">{{ usuario ? t("auth.internalArea") : t("auth.login") }}</a>
          <a v-if="usuario?.permissions?.includes('usuarios.consultar')" href="/interno/usuarios" @click="cerrarMenu">
            {{ t("users.title") }}
          </a>
        </nav>
      </div>
    </header>

    <main class="app-contenido">
      <slot />
    </main>

    <footer class="app-footer">
      <p>SIAM - {{ t("common.systemName") }}</p>
    </footer>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-header {
  --color-foco: #ffffff;
  background: var(--color-header, #1f4a5b);
  color: #fff;
}

.header-contenido {
  max-width: 1200px;
  margin: auto;
  padding: 12px 16px;
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.app-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  text-decoration: none;
}

.header-acciones {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.selector-idioma {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-idioma label {
  color: #fff;
  font-size: 14px;
}

.selector-idioma select {
  min-height: 44px;
  padding: 8px;
  border: 1px solid #fff;
  border-radius: 6px;
  background: var(--color-control, #fff);
  color: var(--color-texto, #111);
  font: inherit;
  max-width: 100%;
}

.boton-tema {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  min-width: 44px;
  min-height: 44px;
  padding: 8px;
  border: 1px solid #fff;
  border-radius: 6px;
  background: transparent;
  color: #fff;
  font-size: 22px;
  cursor: pointer;
}

.boton-tema:hover,
.boton-tema:focus-visible {
  background: var(--color-header-hover, #356579);
}

.app-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-nav a,
.menu-boton {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 8px 12px;
  box-sizing: border-box;
  color: #fff;
  text-decoration: none;
}

.app-nav a:hover {
  background: var(--color-header-hover, #356579);
}

.menu-boton {
  display: none;
  background: transparent;
  border: 1px solid #fff;
  border-radius: 6px;
  font: inherit;
  cursor: pointer;
}

.app-contenido {
  flex: 1;
  width: 100%;
  max-width: 1200px;
  box-sizing: border-box;
  margin: 0 auto;
  padding: 24px 16px;
  min-width: 0;
}

.app-footer {
  padding: 16px;
  background: var(--color-footer, #f1f4f5);
  text-align: center;
  color: var(--color-texto, #263b45);
}

.app-footer p {
  margin: 0;
}

@media (max-width: 767px) {
  .header-contenido {
    padding: 12px;
  }

  .menu-boton {
    display: flex;
  }

  .app-nav {
    display: none;
    flex-direction: column;
    align-items: stretch;
    width: 100%;
    padding-bottom: 12px;
    gap: 4px;
  }

  .app-nav.nav-abierta {
    display: flex;
  }

  .app-nav a {
    justify-content: flex-start;
  }
}

@media (max-width: 380px) {
  .header-acciones {
    gap: 6px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .selector-idioma {
    gap: 4px;
  }

  .selector-idioma label {
    font-size: 12px;
  }

  .selector-idioma select {
    padding: 6px 4px;
    font-size: 13px;
  }

  .menu-boton {
    padding: 8px;
  }
}
</style>
