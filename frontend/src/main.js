
import { createApp } from "vue"
import App from "./App.vue"
import { i18n } from "./i18n/index.js"
import { inicializarTema } from "./theme/index.js"
import "./styles/responsive.css"

const app = createApp(App)

app.use(i18n)

document.documentElement.lang = i18n.global.locale.value
inicializarTema()

app.mount("#app")
