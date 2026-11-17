import { test as base, expect } from '@playwright/test'
import type { Page } from '@playwright/test'
import { readFile } from 'node:fs/promises'

const test = base.extend<{ pageErrors: string[] }>({
  pageErrors: [
    async ({ page }, use) => {
      const errors: string[] = []
      page.on('pageerror', (error) => errors.push(error.message))
      await use(errors)
      expect(errors).toEqual([])
    },
    { auto: true },
  ],
})
const code = (page: Page) =>
  page.getByRole('textbox', { name: 'Código fuente .hor' })
async function compile(page: Page, status = 'Válido') {
  const response = page.waitForResponse(
    (r) => r.url().endsWith('/analyses') && r.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Compilar', exact: true }).click()
  expect((await response).status()).toBe(200)
  await expect(page.locator('.result-meta .badge')).toHaveText(status)
}
async function example(page: Page, id: string) {
  await page.getByRole('combobox', { name: 'Elegir ejemplo' }).selectOption(id)
  const response = page.waitForResponse((r) =>
    r.url().endsWith(`/examples/${id}`),
  )
  await page.getByRole('button', { name: 'Cargar ejemplo' }).click()
  expect((await response).status()).toBe(200)
  await expect(
    page.getByRole('button', { name: 'Cargar ejemplo' }),
  ).toBeEnabled()
}
test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('status')).toHaveText('API conectada')
})

test('editor, API real, tokens, símbolos y horario', async ({ page }) => {
  await expect(code(page)).toBeVisible()
  await compile(page)
  await expect(page.getByRole('columnheader', { name: 'Lexema' })).toBeVisible()
  await page.getByRole('tab', { name: 'Tabla de símbolos' }).click()
  await expect(
    page.getByRole('columnheader', { name: 'Atributos' }),
  ).toBeVisible()
  await page.getByRole('tab', { name: 'Horario resultante' }).click()
  await expect(page.getByText('4 horas semanales')).toBeVisible()
  await page.screenshot({ path: '/tmp/schedule-calendar.png', fullPage: true })
})

test('árbol con ramas, campos y navegación al editor', async ({ page }) => {
  await compile(page)
  await page.getByRole('tab', { name: 'Árbol sintáctico' }).click()
  await expect(page.locator('.react-flow__node').first()).toBeVisible()
  // Un segmento horizontal tiene altura geométrica cero aunque su trazo sea visible.
  await expect(page.locator('.react-flow__edge-path').first()).toHaveAttribute(
    'd',
    /^M/,
  )
  await page.getByRole('button', { name: 'Expandir todo', exact: true }).click()
  await expect(page.locator('.react-flow__node')).toHaveCount(16)
  await page.getByRole('button', { name: 'Acercar árbol', exact: true }).click()
  await page.getByRole('button', { name: 'Ajustar árbol', exact: true }).click()
  await page.locator('.react-flow__node').filter({ hasText: 'Materia' }).click()
  await expect
    .poll(() => page.evaluate(() => window.getSelection()?.toString()))
    .toBe('"COMPILADORES"')
  await page.screenshot({ path: '/tmp/schedule-tree.png', fullPage: true })
})

test('Carolina conserva sesiones y horas de API', async ({ page }) => {
  await example(page, 'carolina')
  await expect(
    page.getByRole('combobox', { name: 'Modo de análisis' }),
  ).toHaveValue('PERSONAL')
  await compile(page)
  await expect(page.getByText('276 de 276 tokens')).toBeVisible()
  await page.getByRole('tab', { name: 'Horario resultante' }).click()
  await expect(page.getByText('29 horas semanales')).toBeVisible()
  await expect(page.locator('.class-block')).toHaveCount(16)
})

test('error semántico real e incompleto tienen diagnósticos', async ({
  page,
}) => {
  await example(page, 'aula-ocupada')
  await compile(page, 'Inválido')
  await expect(
    page.locator('.diagnostic-title').filter({ hasText: 'CHOQUE_AULA' }),
  ).toBeVisible()
  await example(page, 'aula-pendiente')
  await compile(page, 'Incompleto')
  await expect(
    page.locator('.diagnostic-title').filter({ hasText: 'AULA_PENDIENTE' }),
  ).toBeVisible()
})

test('subir .hor editable y preservar código ante UTF-8 inválido', async ({
  page,
}) => {
  const source =
    'HORARIO "Subido" {\r\n INSCRIBIR "ISC_7B_COMPILADORES"\r\n}\r\n'
  await page
    .getByLabel('Seleccionar archivo .hor')
    .setInputFiles({
      name: 'amigo.hor',
      mimeType: 'text/plain',
      buffer: Buffer.from(source),
    })
  await expect(page.locator('.file-name')).toHaveText('amigo.hor')
  await page
    .getByRole('combobox', { name: 'Modo de análisis' })
    .selectOption('PERSONAL')
  await compile(page)
  await page
    .getByLabel('Seleccionar archivo .hor')
    .setInputFiles({
      name: 'malo.hor',
      mimeType: 'text/plain',
      buffer: Buffer.from([255, 255]),
    })
  await expect(page.getByRole('alert')).toContainText('UTF-8')
  await expect(page.locator('.file-name')).toHaveText('amigo.hor')
  await expect(code(page)).toContainText('Subido')
})

test('cambiar entrada marca resultados anteriores y atajo recompila', async ({
  page,
}) => {
  await compile(page)
  await code(page).click()
  await code(page).press('ControlOrMeta+End')
  await page.keyboard.insertText('\n# modificado')
  await expect(
    page.getByText('La entrada o las opciones cambiaron.', { exact: false }),
  ).toBeVisible()
  await code(page).press('ControlOrMeta+Enter')
  await expect(page.locator('.stale-banner')).toHaveCount(0)
  await expect(page.locator('.result-meta .badge')).toHaveText('Válido')
})

test('fallos léxicos y sintácticos no muestran un árbol inventado', async ({
  page,
}) => {
  await example(page, 'error-lexico')
  await compile(page, 'Inválido')
  await expect(
    page
      .locator('.diagnostic-title')
      .filter({ hasText: 'CARACTER_NO_PERMITIDO' }),
  ).toBeVisible()
  await page.getByRole('tab', { name: 'Árbol sintáctico' }).click()
  await expect(page.getByText('No se pudo construir el árbol')).toBeVisible()
  await example(page, 'error-sintactico')
  await compile(page, 'Inválido')
  await expect(
    page.locator('.diagnostic-title').filter({ hasText: 'TOKEN_INESPERADO' }),
  ).toBeVisible()
})

test('reglas no configuradas y auditoría se distinguen de la entrada', async ({
  page,
}) => {
  await page
    .getByRole('combobox', { name: 'Catálogo' })
    .selectOption('isc-26-1-original')
  await compile(page)
  await page.getByRole('tab', { name: 'Errores y advertencias' }).click()
  await expect(page.getByText('Sin diagnósticos en esta vista')).toBeVisible()
  await page.getByRole('button', { name: /^Catálogo / }).click()
  await expect(
    page.locator('.diagnostic-title').filter({ hasText: 'CHOQUE_AULA' }),
  ).toBeVisible()
  await page.getByRole('button', { name: /^Reglas / }).click()
  await expect(
    page.getByRole('cell', { name: 'REGLAS_DOCENTES', exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole('cell', { name: 'CAPACIDAD', exact: true }),
  ).toBeVisible()
  await expect(page.locator('.result-meta .badge')).toHaveText('Válido')
})

test('errores de red conservan el código y no anuncian éxito', async ({
  page,
}) => {
  const before = await code(page).innerText()
  await page.route('**/api/v1/analyses', (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Servicio temporalmente no disponible.' }),
    }),
  )
  await page.getByRole('button', { name: 'Compilar', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText(
    'Servicio temporalmente no disponible',
  )
  await expect(code(page)).toHaveText(before, { useInnerText: true })
  await expect(page.locator('.result-meta .badge')).toHaveCount(0)
})

test('respuesta de API fuera de contrato se rechaza', async ({ page }) => {
  await page.route('**/api/v1/analyses', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '{"status":"VALIDO"}',
    }),
  )
  await page.getByRole('button', { name: 'Compilar', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('contrato esperado')
  await expect(page.locator('.result-meta .badge')).toHaveCount(0)
})

test('borrador se restaura después de recargar y limpiar lo vacía', async ({
  page,
}) => {
  await code(page).fill(
    'HORARIO "Borrador" { INSCRIBIR "ISC_7B_COMPILADORES" }',
  )
  await page
    .getByRole('combobox', { name: 'Modo de análisis' })
    .selectOption('PERSONAL')
  await page.reload()
  await expect(code(page)).toContainText('Borrador')
  await expect(
    page.getByRole('combobox', { name: 'Modo de análisis' }),
  ).toHaveValue('PERSONAL')
  await compile(page)
  await page.getByRole('button', { name: 'Limpiar', exact: true }).click()
  await expect(code(page)).toHaveText('')
  await expect(page.locator('.result-meta .badge')).toHaveCount(0)
  await page.reload()
  await expect(code(page)).toHaveText('')
})

test('tokens después de emoji se enlazan al rango correcto del editor', async ({
  page,
}) => {
  await code(page).fill('HORARIO "😀" { INSCRIBIR "ISC_7B_COMPILADORES" }')
  await page
    .getByRole('combobox', { name: 'Modo de análisis' })
    .selectOption('PERSONAL')
  await compile(page)
  await page.getByRole('button', { name: 'INSCRIBIR', exact: true }).click()
  await expect
    .poll(() => page.evaluate(() => window.getSelection()?.toString()))
    .toBe('INSCRIBIR')
})

test('descargar fuente y resultado conserva datos reales', async ({ page }) => {
  let promise = page.waitForEvent('download')
  await page
    .getByRole('button', { name: 'Descargar código .hor', exact: true })
    .click()
  const source = await promise
  expect(source.suggestedFilename()).toBe('oferta_compiladores.hor')
  expect(await readFile((await source.path())!, 'utf8')).toContain(
    'OFERTA "ISC_7B_COMPILADORES"',
  )
  await compile(page)
  promise = page.waitForEvent('download')
  await page
    .getByRole('button', { name: 'Descargar resultado JSON', exact: true })
    .click()
  const result = JSON.parse(
    await readFile((await (await promise).path())!, 'utf8'),
  )
  expect(result.status).toBe('VALIDO')
  expect(result.ast.kind).toBe('Program')
})

test('edición durante una compilación no se confunde con el resultado anterior', async ({
  page,
}) => {
  let release!: () => void
  const gate = new Promise<void>((resolve) => {
    release = resolve
  })
  await page.route('**/api/v1/analyses', async (route) => {
    const response = await route.fetch()
    await gate
    await route.fulfill({ response }).catch(() => {})
  })
  await page.getByRole('button', { name: 'Compilar', exact: true }).click()
  await code(page).press('ControlOrMeta+End')
  await page.keyboard.insertText('\n# edición posterior')
  release()
  await expect(page.locator('.stale-banner')).toBeVisible()
  await expect(
    page.getByRole('button', { name: 'Descargar resultado JSON' }),
  ).toBeDisabled()
  await expect(code(page)).toContainText('edición posterior')
})

test('cargar un ejemplo lentamente no pisa una edición posterior', async ({
  page,
}) => {
  let release!: () => void
  const gate = new Promise<void>((resolve) => {
    release = resolve
  })
  await page.route('**/api/v1/examples/carolina', async (route) => {
    const response = await route.fetch()
    await gate
    await route.fulfill({ response }).catch(() => {})
  })
  await page.getByRole('button', { name: 'Cargar ejemplo' }).click()
  await code(page).fill('# mantener mi edición')
  release()
  await expect(
    page.getByRole('button', { name: 'Cargar ejemplo' }),
  ).toBeEnabled()
  await expect(code(page)).toHaveText('# mantener mi edición')
})

test('teclado navega pestañas y modal de guía', async ({ page }) => {
  await compile(page)
  await page.getByRole('tab', { name: 'Tokens', exact: true }).focus()
  await page.keyboard.press('ArrowRight')
  await expect(
    page.getByRole('tab', { name: 'Árbol sintáctico' }),
  ).toBeFocused()
  await page.getByRole('button', { name: 'Guía', exact: true }).click()
  await expect(
    page.getByRole('dialog', { name: 'Cómo analizar tu horario' }),
  ).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toBeHidden()
})

test('pantalla pequeña apila paneles y mantiene acciones utilizables', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.getByRole('button', { name: 'Subir .hor' })).toBeVisible()
  await compile(page)
  await page.getByRole('tab', { name: 'Horario resultante' }).click()
  await expect(page.getByText('4 horas semanales')).toBeVisible()
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true)
  await page.screenshot({ path: '/tmp/schedule-mobile.png', fullPage: true })
})
