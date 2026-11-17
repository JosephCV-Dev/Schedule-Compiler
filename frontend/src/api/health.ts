export interface HealthResponse {
  status: 'ok'
  service: 'schedule-compiler'
  language_version: '0.2'
  compiler_available: boolean
}

export async function getHealth(signal: AbortSignal): Promise<HealthResponse> {
  const response = await fetch('/api/v1/health', { signal })
  if (!response.ok) throw new Error('No se pudo consultar la API.')

  const data: unknown = await response.json()
  if (
    typeof data !== 'object' || data === null ||
    !('status' in data) || data.status !== 'ok' ||
    !('service' in data) || data.service !== 'schedule-compiler' ||
    !('language_version' in data) || data.language_version !== '0.2' ||
    !('compiler_available' in data) || typeof data.compiler_available !== 'boolean'
  ) {
    throw new Error('La respuesta no coincide con el contrato de salud de la API.')
  }

  return data as HealthResponse
}
