import { test, expect } from "@playwright/test"

const fields = [
  "object_type",
  "materials_techniques",
  "inscriptions_marks",
  "distinguishing_features",
  "title",
  "subject",
  "date_period",
  "author_maker",
]
const png =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jA1sAAAAASUVORK5CYII="
async function setup(page, language, theme) {
  await page.addInitScript(
    ({ language, theme }) => {
      localStorage.setItem("siam-idioma", language)
      localStorage.setItem("siam-tema", theme)
    },
    { language, theme },
  )
  let piece = {
    id: 1,
    identifier: "f0577edb-462b-4d43-9cdd-3eb8db1c5b89",
    ...Object.fromEntries(
      fields.map((f) => [f, f === "title" ? "Vase" : "Description"]),
    ),
    measurement_value: "12.5000",
    measurement_unit: "cm",
    state: "stored",
    location: "",
    decommissioned: false,
    history: [],
    photos: [],
  }
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url()),
      method = route.request().method()
    const reply = (data, status = 200) =>
      route.fulfill({
        status,
        json: data,
        headers: {
          "Access-Control-Allow-Origin": "http://127.0.0.1:5173",
          "Access-Control-Allow-Credentials": "true",
          "Access-Control-Allow-Headers": "content-type,x-csrftoken",
          "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
        },
      })
    if (method === "OPTIONS") return reply({})
    if (url.pathname.endsWith("/auth/me/"))
      return reply({
        id: 1,
        full_name: "Curator",
        role: "museologo",
        permissions: ["piezas.crear"],
      })
    if (url.pathname.endsWith("/auth/csrf/"))
      return reply({ csrfToken: "test" })
    if (url.pathname.endsWith("/pieces/")) {
      if (method === "POST") {
        piece = { ...piece, ...route.request().postDataJSON() }
        return reply(piece, 201)
      }
      const state = url.searchParams.get("state")
      return reply(!state || state === piece.state ? [piece] : [])
    }
    if (url.pathname.endsWith("/photos/")) {
      const file = route.request().postDataJSON().photos[0]
      if (file.name.endsWith(".txt"))
        return reply({
          results: [
            { index: 0, errors: { non_field_errors: ["invalid_image"] } },
          ],
        })
      piece.photos.push({
        id: piece.photos.length + 1,
        name: file.name,
        data: `data:image/png;base64,${file.content}`,
      })
      return reply({ results: [{ index: 0, id: piece.photos.length }] })
    }
    if (method === "PATCH") {
      const data = route.request().postDataJSON()
      if (data.state === "displayed" && !data.location?.trim())
        return reply({ location: ["required"] }, 400)
      const changes = Object.fromEntries(
        Object.entries(data)
          .filter(([key, value]) => value !== piece[key])
          .map(([key, value]) => [key, { old: piece[key], new: value }]),
      )
      piece = {
        ...piece,
        ...data,
        location:
          data.state === "stored" ? "" : (data.location ?? piece.location),
      }
      piece.history.unshift({
        id: piece.history.length + 1,
        user: "curator@example.com",
        timestamp: "2026-10-31T18:00:00Z",
        changes,
      })
    }
    return reply(piece)
  })
  await page.goto("/interno/coleccion")
  await expect(
    page.getByRole("button", { name: "Vase", exact: true }),
  ).toBeVisible()
}
async function fits(page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true)
}
for (const width of [360, 768, 1280])
  for (const language of ["es", "en"])
    for (const theme of ["claro", "oscuro"]) {
      test(`${width}px ${language} ${theme}: list, validation, detail, edit and photos`, async ({
        page,
      }) => {
        await page.setViewportSize({ width, height: 900 })
        await setup(page, language, theme)
        const es = language === "es"
        const save = es ? "Guardar" : "Save",
          cancel = es ? "Cancelar" : "Cancel"
        await expect(page.locator("html")).toHaveAttribute("data-theme", theme)
        await fits(page)
        await page
          .getByRole("button", {
            name: es ? "Nueva pieza" : "New piece",
            exact: true,
          })
          .click()
        await page.getByRole("button", { name: save, exact: true }).click()
        await expect(page.locator('[aria-invalid="true"]')).toHaveCount(9)
        await fits(page)
        for (const field of fields)
          await page
            .locator(`#${field}`)
            .fill(field === "title" ? "New vase" : "Description")
        await page.locator("#measurement").fill("3.5")
        await page.getByRole("button", { name: save, exact: true }).click()
        await expect(
          page.getByRole("heading", { name: "New vase", exact: true }),
        ).toBeVisible()
        await expect(
          page.locator(".collection").getByRole("status"),
        ).toContainText(es ? "guardada" : "saved")
        await fits(page)
        await page.locator("#piece-state").selectOption("displayed")
        await page
          .locator("#piece-state")
          .locator("..")
          .getByRole("button", { name: save, exact: true })
          .click()
        await expect(page.locator("#location")).toHaveAttribute(
          "aria-invalid",
          "true",
        )
        await page.locator("#location").fill("Room A, case 2")
        await page
          .locator("#piece-state")
          .locator("..")
          .getByRole("button", { name: save, exact: true })
          .click()
        await expect(
          page.locator("dd").filter({ hasText: "Room A, case 2" }),
        ).toBeVisible()
        await page
          .getByRole("button", { name: es ? "Editar" : "Edit", exact: true })
          .click()
        await page.locator("#title").fill("Cancelled title")
        await page.getByRole("button", { name: cancel, exact: true }).click()
        await expect(
          page.getByRole("heading", { name: "New vase", exact: true }),
        ).toBeVisible()
        await page
          .getByRole("button", { name: es ? "Editar" : "Edit", exact: true })
          .click()
        await page.locator("#title").fill("Edited vase")
        await page.getByRole("button", { name: save, exact: true }).click()
        await expect(
          page.getByRole("heading", { name: "Edited vase", exact: true }),
        ).toBeVisible()
        await page.locator("#photos").setInputFiles([
          {
            name: "vase.png",
            mimeType: "image/png",
            buffer: Buffer.from(png, "base64"),
          },
          {
            name: "invalid.txt",
            mimeType: "text/plain",
            buffer: Buffer.from("invalid"),
          },
        ])
        await expect(page.locator(".photos img")).toHaveCount(1)
        await expect(
          page.getByText(
            es ? "invalid.txt: El archivo" : "invalid.txt: The file",
            { exact: false },
          ),
        ).toBeVisible()
        await page.locator(".photos button").click()
        await expect(page.getByRole("dialog")).toBeVisible()
        await page
          .getByRole("button", { name: es ? "Cerrar" : "Close", exact: true })
          .click()
        await fits(page)
        await page.locator("#piece-state").selectOption("stored")
        await expect(page.locator("#location")).toHaveCount(0)
        await page
          .locator("#piece-state")
          .locator("..")
          .getByRole("button", { name: save, exact: true })
          .click()
        await expect(
          page.locator("dd").filter({ hasText: "Room A, case 2" }),
        ).toHaveCount(0)
        await page
          .getByRole("button", {
            name: es ? "Volver a la colecci\u00f3n" : "Back to collection",
            exact: true,
          })
          .click()
        await page.locator("#state-filter").selectOption("displayed")
        await expect(page.locator(".pieces li")).toHaveCount(0)
        await page.locator("#state-filter").selectOption("stored")
        await expect(
          page.getByRole("button", { name: "Edited vase", exact: true }),
        ).toBeVisible()
        await fits(page)
      })
    }
