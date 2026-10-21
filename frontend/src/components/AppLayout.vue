
<script setup>
import { ref } from "vue"

// Controla si el menú móvil está abierto o cerrado.
const menuAbierto = ref(false)

// Enlaces de navegación del sistema.
const enlaces = [
  { nombre: "Inicio", ruta: "/" },
  { nombre: "Información del museo", ruta: "/informacion" },
  { nombre: "Eventos", ruta: "/eventos" },
]

function cerrarMenu() {
  menuAbierto.value = false
}
</script>

<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-contenido">
        <a class="app-logo" href="/" @click="cerrarMenu">
          SIAM
        </a>

        <button
          class="menu-boton"
          type="button"
          aria-controls="navegacion-principal"
          :aria-expanded="menuAbierto"
          @click="menuAbierto = !menuAbierto"
        >
          {{ menuAbierto ? "Cerrar menú" : "Menú" }}
        </button>

        <nav
          id="navegacion-principal"
          class="app-nav"
          :class="{ 'nav-abierta': menuAbierto }"
          aria-label="Navegación principal"
        >
          <a
            v-for="enlace in enlaces"
            :key="enlace.ruta"
            :href="enlace.ruta"
            @click="cerrarMenu"
          >
            {{ enlace.nombre }}
          </a>
        </nav>
      </div>
    </header>

    <main class="app-contenido">
      <slot />
    </main>

    <footer class="app-footer">
      <p>SIAM - Sistema de Información y Analítica Museal</p>
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
  background: #1f4a5b;
  color: #fff;
}

.header-contenido {
  max-width: 1200px;
  margin: auto;
  padding: 0 16px;
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


.app-nav {
  display: flex;
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
  background: #356579;
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
  background: #f1f4f5;
  text-align: center;
  color: #263b45;
}

.app-footer p {
  margin: 0;
}

@media (max-width: 767px) {
  .menu-boton {
    display: flex;
  }

  .app-nav {
    display: none;
    flex-direction: column;
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
</style>
