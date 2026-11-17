import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { compile } from 'json-schema-to-typescript'

const contracts = new URL('../../contracts/', import.meta.url)
const output = new URL('../src/api/generated/', import.meta.url)
const entries = [
  ['analysis-request', 'AnalysisRequest'],
  ['analysis-response', 'AnalysisResponse'],
  ['catalog-list', 'CatalogList'],
  ['example-list', 'ExampleList'],
  ['example', 'Example'],
]
const check = process.argv.includes('--check')
if (!check) await mkdir(output, { recursive: true })
for (const [file, title] of entries) {
  const schema = JSON.parse(
    await readFile(new URL(`${file}.schema.json`, contracts), 'utf8'),
  )
  const text = await compile(schema, title, {
    bannerComment: '/* Generado desde contracts/. No editar a mano. */',
    additionalProperties: false,
    style: { singleQuote: true, semi: false },
  })
  const target = new URL(`${title}.ts`, output)
  if (check) {
    if ((await readFile(target, 'utf8').catch(() => '')) !== text)
      throw new Error(`Tipos desactualizados: ${fileURLToPath(target)}`)
  } else await writeFile(target, text)
}
console.log(
  `Tipos de ${entries.length} contratos ${check ? 'verificados' : 'generados'}.`,
)
