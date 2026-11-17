import Ajv2020 from 'ajv/dist/2020'
import analysisSchema from '../../../contracts/analysis-response.schema.json'
import catalogSchema from '../../../contracts/catalog-list.schema.json'
import examplesSchema from '../../../contracts/example-list.schema.json'
import exampleSchema from '../../../contracts/example.schema.json'
import type {
  AnalysisRequest,
  AnalysisResponse,
  CatalogList,
  ExampleList,
  Example,
} from './types'

const ajv = new Ajv2020({ strict: false })
const validateAnalysis = ajv.compile<AnalysisResponse>(analysisSchema)
const validateCatalogs = ajv.compile<CatalogList>(catalogSchema)
const validateExamples = ajv.compile<ExampleList>(examplesSchema)
const validateExample = ajv.compile<Example>(exampleSchema)

async function request(
  path: string,
  signal: AbortSignal,
  body?: AnalysisRequest,
): Promise<unknown> {
  const response = await fetch(`/api/v1${path}`, {
    signal,
    method: body ? 'POST' : 'GET',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(
      typeof data?.detail === 'string'
        ? data.detail
        : response.status === 422
          ? 'La solicitud no coincide con el contrato de análisis.'
          : `No se pudo completar la solicitud (HTTP ${response.status}). Comprueba que el backend esté encendido.`,
    )
  }
  return response.json().catch(() => {
    throw new Error('La API devolvió una respuesta que no es JSON.')
  })
}

export async function analyzeSource(
  body: AnalysisRequest,
  signal: AbortSignal,
): Promise<AnalysisResponse> {
  const data = await request('/analyses', signal, body)
  if (!validateAnalysis(data))
    throw new Error(
      'La respuesta de análisis no coincide con el contrato esperado.',
    )
  return data
}
export async function getCatalogs(signal: AbortSignal): Promise<CatalogList> {
  const data = await request('/catalogs', signal)
  if (!validateCatalogs(data))
    throw new Error('No se pudo interpretar la lista de catálogos.')
  return data
}
export async function getExamples(signal: AbortSignal): Promise<ExampleList> {
  const data = await request('/examples', signal)
  if (!validateExamples(data))
    throw new Error('No se pudo interpretar la lista de ejemplos.')
  return data
}
export async function getExample(
  id: string,
  signal: AbortSignal,
): Promise<Example> {
  const data = await request(`/examples/${encodeURIComponent(id)}`, signal)
  if (!validateExample(data))
    throw new Error('No se pudo interpretar el ejemplo.')
  return data
}
