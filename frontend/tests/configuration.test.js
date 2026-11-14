import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { afterEach, test } from "node:test"
import { compileScript, parse } from "@vue/compiler-sfc"
import { createRenderer, nextTick } from "vue"
import { i18n } from "../src/i18n/index.js"

const source = await readFile(new URL("../src/components/ConfiguracionMuseo.vue", import.meta.url), "utf8")
const { descriptor } = parse(source)
const api = {}
globalThis.__configurationTestApi = api
const compiled = compileScript(descriptor, { id: "configuration-test" }).content
  .replaceAll('from "vue"', `from ${JSON.stringify(import.meta.resolve("vue"))}`)
  .replaceAll('from "vue-i18n"', `from ${JSON.stringify(import.meta.resolve("vue-i18n"))}`)
  .replace('import { solicitar, enviar } from "../api.js"', `
    const solicitar = (...args) => globalThis.__configurationTestApi.solicitar(...args)
    const enviar = (...args) => globalThis.__configurationTestApi.enviar(...args)
  `)
const { default: component } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`)
const defaults = {
  museum_name: "Museum", address: "Central street", location: "Alajuela", default_language: "es",
  opening_hours: Object.fromEntries(Array.from({ length: 7 }, (_, day) => [day, {
    opens: day === 1 ? null : "09:00", closes: day === 1 ? null : "17:00",
  }])),
}
const response = (body, status = 200) => new Response(JSON.stringify(body), { status })
const configuration = (values = defaults) => response({ values, defaults })
const flush = async () => { await new Promise(setImmediate); await nextTick() }
const apps = []

async function mount() {
  api.solicitar ??= async () => configuration()
  api.enviar ??= async (_path, values) => configuration(values)
  const events = []
  let state
  const renderer = createRenderer({
    createComment: () => ({}), insert() {}, remove() {},
    parentNode: () => null, nextSibling: () => null,
  })
  const app = renderer.createApp({
    setup() {
      state = component.setup({}, { expose() {}, emit: (...args) => events.push(args) })
      return () => null
    },
  })
  app.use(i18n)
  app.mount({})
  apps.push(app)
  state.confirmacion.value = {
    open: false,
    showModal() { this.open = true },
    close() { this.open = false },
  }
  await flush()
  return { state, events }
}

afterEach(() => {
  for (const app of apps.splice(0)) app.unmount()
  delete api.solicitar
  delete api.enviar
})

test("loads independent editable values and can retry a failed load", async () => {
  api.solicitar = async () => { throw new Error("offline") }
  const { state } = await mount()
  assert.equal(state.error.value, "configuration.loadError")
  assert.equal(state.cargando.value, false)
  api.solicitar = async () => configuration()
  await state.cargar()
  state.valores.value.location = "Heredia"
  assert.equal(state.originales.value.location, "Alajuela")
  assert.equal(state.hayCambios.value, true)
})

test("cancel restores saved values without making a request", async () => {
  let requests = 0
  api.enviar = async () => { requests++ }
  const { state } = await mount()
  state.valores.value.museum_name = "Draft"
  state.cambiarCierre(0, true)
  state.cancelar()
  assert.equal(state.valores.value.museum_name, defaults.museum_name)
  assert.equal(state.valores.value.opening_hours[0].opens, "09:00")
  assert.equal(state.hayCambios.value, false)
  assert.equal(requests, 0)
})

test("individual defaults stay in the draft until confirmed save", async () => {
  api.solicitar = async () => configuration({ ...defaults, museum_name: "Saved museum" })
  let requests = 0
  api.enviar = async (_path, values, method) => {
    requests++
    assert.equal(method, "PATCH")
    return configuration(values)
  }
  const { state } = await mount()
  state.valores.value.location = "Heredia"
  state.restaurar("museum_name")
  assert.equal(state.valores.value.museum_name, defaults.museum_name)
  assert.equal(state.valores.value.location, "Heredia")
  assert.equal(requests, 0)
  state.cambiarCierre(0, true)
  state.restaurar("opening_hours")
  state.valores.value.opening_hours[0].opens = "10:00"
  assert.equal(state.predeterminados.value.opening_hours[0].opens, "09:00")
  await state.guardar()
  assert.equal(requests, 0)
  await state.pedirConfirmacion()
  assert.equal(state.confirmacion.value.open, true)
  state.confirmacion.value.close()
  await state.guardar()
  assert.equal(requests, 0)
  await state.pedirConfirmacion()
  await state.guardar()
  assert.equal(requests, 1)
  assert.equal(state.mensaje.value, "configuration.saved")
  assert.equal(state.hayCambios.value, false)
  state.valores.value.location = "Draft"
  state.cancelar()
  assert.equal(state.valores.value.location, "Heredia")
})

test("invalid hours prevent confirmation; closed days send null hours", async () => {
  const { state } = await mount()
  state.valores.value.opening_hours[0] = { opens: "17:00", closes: "09:00" }
  await state.pedirConfirmacion()
  assert.equal(state.confirmacion.value.open, false)
  assert.equal(state.errores.value.opening_hours[0], true)
  state.cambiarCierre(0, true)
  await state.pedirConfirmacion()
  assert.equal(state.confirmacion.value.open, true)
  assert.deepEqual(state.valores.value.opening_hours[0], { opens: null, closes: null })
})

test("server validation and connection failures preserve the draft for retry", async () => {
  const { state } = await mount()
  state.valores.value.museum_name = "Draft"
  api.enviar = async () => response({ museum_name: ["Invalid"] }, 400)
  await state.pedirConfirmacion()
  await state.guardar()
  assert.equal(state.error.value, "configuration.invalid")
  assert.ok(state.errores.value.museum_name)
  api.enviar = async () => { throw new Error("offline") }
  await state.pedirConfirmacion()
  await state.guardar()
  assert.equal(state.error.value, "configuration.saveError")
  assert.equal(state.valores.value.museum_name, "Draft")
  assert.equal(state.guardando.value, false)
  api.enviar = async (_path, values) => configuration(values)
  await state.pedirConfirmacion()
  await state.guardar()
  assert.equal(state.originales.value.museum_name, "Draft")
})

test("expired sessions and denied access clear the form and notify App", async () => {
  for (const [status, event] of [[401, "sesion-expirada"], [403, "sin-acceso"]]) {
    api.solicitar = async () => response({}, status)
    const initial = await mount()
    assert.deepEqual(initial.events, [[event]])
    assert.equal(initial.state.valores.value, null)
    api.solicitar = async () => configuration()
    const { state, events } = await mount()
    state.valores.value.location = "Draft"
    api.enviar = async () => response({}, status)
    await state.pedirConfirmacion()
    await state.guardar()
    assert.deepEqual(events, [[event]])
    assert.equal(state.valores.value, null)
  }
})

test("a pending save cannot be submitted twice", async () => {
  const { state } = await mount()
  state.valores.value.location = "Heredia"
  let finish
  let requests = 0
  api.enviar = (_path, values) => {
    requests++
    return new Promise(resolve => { finish = () => resolve(configuration(values)) })
  }
  await state.pedirConfirmacion()
  const pending = state.guardar()
  await state.guardar()
  assert.equal(requests, 1)
  assert.equal(state.guardando.value, true)
  finish()
  await pending
  assert.equal(state.guardando.value, false)
})
