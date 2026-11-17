/* Generado desde contracts/. No editar a mano. */

export type Source = string
export type SourceName = string
export type LanguageVersion = '0.2'
export type CatalogId = 'isc-26-1-trabajo' | 'isc-26-1-original'
export type PolicyId = 'proyecto-v0.2'
export type Scope = 'PERSONAL' | 'PROPUESTA'

export interface AnalysisRequest {
  source: Source
  source_name?: SourceName
  language_version?: LanguageVersion
  catalog_id?: CatalogId
  policy_id?: PolicyId
  scope?: Scope
}
