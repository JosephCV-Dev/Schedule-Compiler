/* Generado desde contracts/. No editar a mano. */

export type Id = string
export type Title = string
export type SourceName = string
export type Scope = 'PERSONAL' | 'PROPUESTA'
export type ExampleList = ExampleSummaryResponse[]

export interface ExampleSummaryResponse {
  id: Id
  title: Title
  source_name: SourceName
  scope: Scope
}
