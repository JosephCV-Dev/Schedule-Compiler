/* Generado desde contracts/. No editar a mano. */

export type Id = string
export type Title = string
export type SourceName = string
export type Scope = 'PERSONAL' | 'PROPUESTA'
export type Source = string

export interface ExampleResponse {
  id: Id
  title: Title
  source_name: SourceName
  scope: Scope
  source: Source
}
