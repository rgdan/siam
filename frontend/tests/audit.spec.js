import { test, expect } from "@playwright/test"

for (const language of ["es", "en"])
  for (const theme of ["claro", "oscuro"])
    for (const width of [360, 1280])
    test(`${language} ${theme} ${width}px: readable records and piece filter`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 })
      await page.addInitScript(({ language, theme }) => {
        localStorage.setItem("siam-idioma", language)
        localStorage.setItem("siam-tema", theme)
      }, { language, theme })
      const entries = [
        { id: 7, action_type: "modify", entity: "user", changes: { is_active: { old: true, new: false }, credential_reset: { old: null, new: true }, last_login: { old: null, new: "2026-10-31T18:00:00Z" } } },
        { id: 6, action_type: "modify", entity: "system_parameter", changes: { custom_setting: { old: { enabled: false }, new: { enabled: true } } } },
        { id: 5, action_type: "modify", entity: "piece", changes: { state: { old: "stored", new: "displayed" }, location: { old: "", new: "Room A " + "x".repeat(150) } } },
        { id: 4, action_type: "modify", entity: "piece", changes: { photos: { old: [1], new: [2, 3] } } },
        { id: 3, action_type: "login", entity: "user", changes: {} },
        { id: 2, action_type: "modify", entity: "piece", changes: { title: { old: "Vase", new: "Updated vase" } } },
        { id: 1, action_type: "create", entity: "piece", changes: { title: { old: null, new: "Vase" } } },
      ].map(entry => ({ ...entry, entity_id: "1", user: 1, role: "museologo", timestamp: "2026-10-31T18:00:00Z" }))
      await page.route("**/api/**", async route => {
        const url = new URL(route.request().url())
        if (url.pathname.endsWith("/auth/me/"))
          return route.fulfill({ json: { id: 1, full_name: "Admin", role: "administrador_sistema", permissions: ["bitacora.consultar"] } })
        if (url.pathname.endsWith("/audit/")) {
          const entity = url.searchParams.get("entity")
          const results = entries.filter(entry => !entity || entry.entity === entity)
          return route.fulfill({ json: { count: results.length, results, next: null, previous: null } })
        }
        return route.fulfill({ json: {} })
      })
      await page.goto("/interno/bitacora")
      const es = language === "es"
      await expect(page.locator(".registros li")).toHaveCount(entries.length)
      await expect(page.locator("pre")).toHaveCount(0)
      const user = page.locator(".registros li").first()
      await expect(user.getByRole("rowheader", { name: es ? "Contraseña restablecida" : "Password reset" })).toBeVisible()
      await expect(user.getByRole("row").filter({ hasText: es ? "Cuenta activa" : "Active account" })).toContainText("No")
      const loginDate = user.getByRole("row").filter({ hasText: es ? "Último inicio de sesión" : "Last sign in" })
      await expect(loginDate).toContainText("2026")
      await expect(loginDate).not.toContainText("T18:00:00Z")
      await expect(page.locator(".registros li").nth(1).getByRole("table")).toContainText("enabled:")
      const request = page.waitForRequest(request => new URL(request.url()).searchParams.get("entity") === "piece")
      await page.getByLabel(language === "es" ? "Entidad" : "Entity", { exact: true }).selectOption("piece")
      await page.getByRole("button", { name: language === "es" ? "Filtrar" : "Filter", exact: true }).click()
      await request
      await expect(page.locator(".registros li")).toHaveCount(4)
      await expect(page.locator(".registros li").first()).toContainText(language === "es" ? "Pieza #1" : "Piece #1")
      const state = page.locator(".registros li").first()
      await expect(state.getByRole("table")).toContainText(es ? "En almacenamiento" : "In storage")
      await expect(state.getByRole("table")).toContainText(es ? "En exhibición" : "On display")
      const photos = page.locator(".registros li").nth(1)
      await expect(photos.locator(".resumen")).toHaveText(es ? "Fotografías agregadas: 2. Fotografías eliminadas: 1." : "Photographs added: 2. Photographs removed: 1.")
      await expect(photos.getByRole("table")).toContainText(es ? "Fotografía #1" : "Photograph #1")
      const edited = page.locator(".registros li").nth(2)
      await expect(edited.getByRole("heading")).toContainText("Updated vase")
      await expect(edited.locator(".resumen")).toContainText(es ? "Título" : "Title")
      await expect(edited.getByRole("cell", { name: "Vase", exact: true })).toBeVisible()
      await expect(edited.getByRole("cell", { name: "Updated vase", exact: true })).toBeVisible()
      await edited.locator("summary").click()
      await expect(edited.getByRole("table")).toBeHidden()
      await edited.locator("summary").press("Enter")
      await expect(edited.getByRole("table")).toBeVisible()
      const created = page.locator(".registros li").last()
      await expect(created.getByRole("heading")).toContainText("Vase")
      await expect(created.locator(".resumen")).toHaveText(es ? "Campos registrados: 1." : "Recorded fields: 1.")
      await expect(created.getByRole("columnheader", { name: es ? "Valor registrado" : "Recorded value" })).toBeVisible()
      await expect(created.getByRole("columnheader", { name: es ? "Antes" : "Before" })).toHaveCount(0)
      await page.getByRole("button", { name: language === "es" ? "Limpiar filtros" : "Clear filters", exact: true }).click()
      await expect(page.locator(".registros li")).toHaveCount(entries.length)
      await expect(page.locator("#filtro-entidad")).toHaveValue("")
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    })
