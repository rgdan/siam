import { createApp } from "vue"
import App from "./App.vue"
import { i18n } from "./i18n/index.js"
import "./styles/responsive.css"

// Conecta el componente raíz con el contenedor #app de index.html.
const app = createApp(App)

// Incorpora el sistema de traducciones.
app.use(i18n)

// Establece el idioma inicial del documento.
document.documentElement.lang = i18n.global.locale.value

// Muestra la aplicación.
app.mount("#app")
